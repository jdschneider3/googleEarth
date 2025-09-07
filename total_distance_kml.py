"""
total_distance_kml.py

Summary:
    For the given .kml file, a total distance in miles is returned based on optional parameters/prompts.

Arguments:
    1) [Required] .kml file path  
    2) [Optional, prompted if not entered] .KML Folder name to calculate total distance on
    3) [Optional, prompted if not entered] name of the Placemark in the folder to calculate total distance on 

Notes:
    Default File Path to Google Earth myplaces.kml is in regedit: HKEY_CURRENT_USER\Software\Google\Google Earth Pro\KMLPath 
"""
    
import sys
import os
import argparse
from lxml import etree
from geopy.distance import geodesic

ns = {"kml": "http://www.opengis.net/kml/2.2",
      "gpx": "http://www.topografix.com/GPX/1/1"}

def check_file_extension(filename, extension):
    if not filename.lower().endswith(extension):
        raise argparse.ArgumentTypeError(f"Invalid file type: Only {extension} files are allowed.")
    if not os.path.isfile(filename):
        raise argparse.ArgumentTypeError(f"File '{filename}' does not exist.")
    return filename  # Return the valid filename

def check_kml_file(filename):
    return check_file_extension(filename, ".kml")

sum_all_distance = 0

def calculate_placemark_distance(placemark):

    # Extract coordinates
    placemark_coordinates = placemark.find(".//kml:coordinates", namespaces=ns).text.strip()
    
    coord_pair_counter = 0
    sum_placemark_distance = 0
    last_coord_pair_lat, last_coord_pair_long = None, None
    
    # Iterate across the coordinate pairs to calculate the total distance traveled
    for curr_coord_pair in placemark_coordinates.split(',0'):
        curr_coord_pair = curr_coord_pair.strip()

        # On the first coordinate pair, we do not calculate distance
        if coord_pair_counter == 0:
            last_coord_pair_lat = curr_coord_pair.split(',', 1)[1].strip()
            last_coord_pair_long = curr_coord_pair.split(',', 1)[0].strip()

        # Calculate distance traveled between the last and current coordinate pair
        else:
            if len(curr_coord_pair) > 1:
                curr_coord_pair_lat = curr_coord_pair.split(',', 1)[1].strip()
                curr_coord_pair_long = curr_coord_pair.split(',', 1)[0].strip()
                
                last_coordinate = (float(last_coord_pair_lat), float(last_coord_pair_long))
                curr_coordinate = (float(curr_coord_pair_lat), float(curr_coord_pair_long))
                
                coord_distance = geodesic(last_coordinate, curr_coordinate).miles
                
                sum_placemark_distance += coord_distance

                # Update the last coordinate pair for the next iteration
                last_coord_pair_lat = curr_coord_pair_lat
                last_coord_pair_long = curr_coord_pair_long
                
        coord_pair_counter += 1
    
    return sum_placemark_distance

#Begin total_distance_kml.py

# Handle Arguments
parser = argparse.ArgumentParser(description="For the given parameters, a total distance in miles is returned.")
parser.add_argument("-i", "--kml", type=check_kml_file, required=True, help="Input (.kml) file path")
parser.add_argument("-f", "--folder", type=str, help="Folder to calculate distance on")
parser.add_argument("-p", "--placemark", type=str, help="Placemark inside of Folder to calculate distance on")
args = parser.parse_args()

# Validate arguments
if not args.folder and args.placemark:
    print("Error: Folder must also be specified, when specifying a Placemark. Exiting...")
    sys.exit(1)

# Parse the KML file
tree = etree.parse(args.kml)
root = tree.getroot()
my_places_folder = root.find(".//kml:Folder[kml:name='My Places']", ns)
subfolders = my_places_folder.findall("kml:Folder", ns)

# Prompt user to select a folder
selected_folder = None

if not args.folder:

    # Create a list of folder names
    folder_options = []
    for index, subfolder in enumerate(subfolders):
        name_element = subfolder.find("kml:name", ns)
        folder_name = name_element.text if name_element is not None else f"Unnamed Folder {index}"
        folder_options.append((index, folder_name))

    while selected_folder is None:
        print("Select a folder to iterate through:")
        for idx, name in folder_options:
            print(f"{idx + 1}. {name}")

        try:
            choice = int(input("Enter the number of the folder you want to process: ")) - 1
            if 0 <= choice < len(folder_options):
                selected_folder = subfolders[choice]
                print(f"\nYou selected: {folder_options[choice][1]}")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input. Please enter a number.")
else:
    selected_folder = my_places_folder.find(".//kml:Folder[kml:name='" + args.folder + "']", namespaces=ns)

    if selected_folder is None:
        print("Error: The folder indicated in arguments was not found in the .KML. Exiting...")
        sys.exit(1)

placemarks_in_folder = selected_folder.xpath(".//kml:Placemark", namespaces=ns)

# Prompt user to select a Placemark
selected_placemark = None

if not args.placemark:
    
    # Create a list of Placemark names
    placemark_options = [(0, "<All Placemarks>")]  # Insert "All Placemarks" as option 0
    for index, placemark in enumerate(placemarks_in_folder):
        name_element = placemark.find("kml:name", ns)
        placemark_name = name_element.text if name_element is not None else f"Unnamed Placemark {index}"
        placemark_options.append((index + 1, placemark_name))  # Index starts from 1 for Placemarks
    
    while selected_placemark is None:
        print("Select a Placemark to calculate distance on. Type 0 to calculate distance on ALL Placemarks in the folder: ")

        # Print options for placemarks
        for idx, name in placemark_options:
            print(f"{idx}. {name}")  # Regular placemarks, idx starts from 0 for "All Placemarks"

        try:
            choice = input("Enter the number of the Placemark you want to process (or '0' for ALL Placemarks): ").strip()

            # Try to parse the input as a number
            choice = int(choice)
            if 0 <= choice < len(placemark_options):
                if choice == 0:
                    selected_placemark = "ALL"  # Special case for "All Placemarks"
                    print(f"\nYou selected: {placemark_options[0][1]}")
                else:
                    selected_placemark = placemarks_in_folder[choice - 1]  # Adjust for the fact that index 0 is "All Placemarks"
                    print(f"\nYou selected: {placemark_options[choice][1]}")  # Print selected Placemark's name
            else:
                print("Invalid selection. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a valid number or '0' for all.")

    if selected_placemark == "ALL":

        # Process all Placemarks in the folder
        print("Calculating distance for all Placemarks...")
        for placemark in placemarks_in_folder:
            placemark_distance = calculate_placemark_distance(placemark)
            sum_all_distance += placemark_distance
    else:
        print("Calculating distance for the selected Placemark...")
        sum_all_distance = calculate_placemark_distance(selected_placemark)

else:

    # The name of the Placemark will be passed in.
    selected_placemark = selected_folder.find(".//kml:Placemark[kml:name='" + args.placemark + "']", namespaces=ns)
    
    if selected_placemark is None:
        print("Error: The Placemark name indicated in the arguments was not found in the .KML. Exiting...")
        sys.exit(1)
    
    sum_all_distance = calculate_placemark_distance(selected_placemark)

print("Total Distance: " + str(sum_all_distance))