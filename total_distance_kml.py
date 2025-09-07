"""
total_distance_kml.py

Summary:
    For the given .kml file, a total distance in miles is returned based on optional parameters/prompts.

Arguments:
    1) [Required] -i: .kml file path  
    2) [Optional] -f: Filepath to the .KML Folder to calculate total distance on
    3) [Optional] -p: Name of the Path in the Folder to calculate total distance on 
    4) [Optional] -r: Recursive Mode (Calculates total distance on all Paths within Folder + Sub-Folders)
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

def find_folder(root_folder, path):
    parts = path.split("/")
    current = root_folder
    for part in parts:
        next_folder = None
        for f in current.findall("kml:Folder", ns):
            name_element = f.find("kml:name", ns)
            if name_element is not None and name_element.text == part:
                next_folder = f
                break
        if next_folder is None:
            return None 
        current = next_folder
    return current

def calculate_path_distance(path):

    # Extract coordinates
    path_coordinates = path.find(".//kml:coordinates", ns)
    
    if path_coordinates is None:
        return 0
    
    path_coord_text = "".join(path_coordinates.itertext()).strip()

    if not path_coord_text:
        return 0

    coord_pair_counter = 0
    sum_path_distance = 0
    last_coord_pair_lat, last_coord_pair_long = None, None
    
    # Iterate across the coordinate pairs to calculate the total distance traveled
    for curr_coord_pair in path_coord_text.split(',0'):
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
                
                sum_path_distance += coord_distance

                # Update the last coordinate pair for the next iteration
                last_coord_pair_lat = curr_coord_pair_lat
                last_coord_pair_long = curr_coord_pair_long
                
        coord_pair_counter += 1
    
    return sum_path_distance

def sum_calculate_path_distance(all_paths):
    sum_distance = 0
    for path in all_paths:
        sum_distance += calculate_path_distance(path)   
    return sum_distance

def folder_name(folder):
    name_element = folder.find("kml:name", ns)
    if name_element is not None and name_element.text:
        return name_element.text.strip()
    else:
        return "Unnamed Folder"

def prompt_user_selected_folder(starting_folder):
    
    current_folder = starting_folder
    
    while True:

        numPaths = len(current_folder.findall("kml:Placemark[kml:LineString]", ns))
        print("\nCurrent Folder: " + folder_name(current_folder) + " ( " + str(numPaths) + " Path(s) )")
        subfolders = current_folder.findall("kml:Folder", ns)

        if not subfolders:
            return current_folder

        # Create a list of folder names
        folder_options = []
        include_current = False

        if numPaths is not None and numPaths > 0: 
            folder_options = [(0, "<Current Folder>")]
            include_current = True

        for index, subfolder in enumerate(subfolders):
            folder_options.append((index + 1, folder_name(subfolder)))

        selected_folder = None
        while selected_folder is None:
            print("\nSelect a folder:")
            for idx, name in folder_options:
                print(f"{idx}. {name}")

            try:

                choice = int(input("\nEnter the number of the folder you want to process: ").strip())

                if include_current:
                    if 0 <= choice < len(folder_options):
                        if choice == 0:
                            return current_folder
                        else:
                            selected_folder = subfolders[choice - 1]
                            print(f"\nYou selected: {folder_options[choice][1]}\n")
                    else:
                        raise ValueError
                else:
                    if 1 <= choice <= len(folder_options):
                        selected_folder = subfolders[choice - 1]
                        print(f"\nYou selected: {folder_options[choice - 1][1]}\n")
                    else:
                        raise ValueError
                    
            except ValueError:
                print("Invalid selection. Please enter a valid number.")

        current_folder = selected_folder

def main():
    
    sum_all_distance = 0

    # Handle Arguments
    parser = argparse.ArgumentParser(description="For the given parameters, a total distance in miles is returned.")
    parser.add_argument("-i", "--kml", type=check_kml_file, required=True, help="Input (.kml) file path")
    parser.add_argument("-f", "--folder", type=str, help="Filepath to the folder to calculate distance on")
    parser.add_argument("-p", "--path", type=str, help="Path inside of Folder to calculate distance on")
    parser.add_argument("-r", "--recursive", action="store_true", help="Calculate distance on all Paths within Folder + Sub-Folders")
    args = parser.parse_args()

    # Validate arguments
    if not args.folder and args.path:
        print("Error: Folder must also be specified, when specifying a Path. Exiting...")
        sys.exit(1)

    # Parse the KML file
    tree = etree.parse(args.kml)
    root = tree.getroot()
    top_folder = root.find(".//kml:Document", ns).find("kml:Folder", ns)

    # Folder Selection
    selected_folder = None

    if not args.folder and not args.path and args.recursive :
    
        # Calculate total distance on all Paths within the entire file.
        selected_folder = top_folder

    else:
        
        if args.folder:

            # Use the Folder filepath passed in as the argument
            selected_folder = find_folder(top_folder, args.folder)

            if selected_folder is None:
                print("Error: The folder indicated in arguments was not found in the .KML. Exiting...")
                sys.exit(1)

        else:

            # Prompt user to select a Folder
            selected_folder = prompt_user_selected_folder(top_folder)
            
    # Path Selection
    selected_path = None

    if args.path:

        # Use the Path Name passed in as the argument
        selected_path = selected_folder.find("kml:Placemark[kml:name='" + args.path + "']", ns)
        
        if selected_path is None or selected_path.find("kml:LineString", ns) is None:
            print("Error: The Path name indicated in the arguments was not found in the .KML. Exiting...")
            sys.exit(1)
        
        sum_all_distance = calculate_path_distance(selected_path)

    else:

        if args.recursive:

            # Process all Paths in the selected Folder recursively            
            print("Calculating distance for all Paths (Recursive Mode)...")
            sum_all_distance = sum_calculate_path_distance(selected_folder.findall(".//kml:Placemark[kml:LineString]", ns))

        else:

            # Prompt user to select a Path
            paths_in_folder = selected_folder.findall("kml:Placemark[kml:LineString]", ns)

            # Create a list of Path names
            path_options = [(0, "<All Paths>")]
            for index, path in enumerate(paths_in_folder):
                name_element = path.find("kml:name", ns)
                path_name = name_element.text if name_element is not None else f"Unnamed path {index}"
                path_options.append((index + 1, path_name))  # Index starts from 1 for Paths
            
            while selected_path is None:
                print("\nSelect a Path to calculate distance on. Type 0 to calculate distance on ALL PATHS in the folder: ")

                # Print options for Paths
                for idx, name in path_options:
                    print(f"{idx}. {name}")  # Regular Paths, idx starts from 0 for "All Paths"

                try:
                
                    choice = int(input("\nEnter the number of the path you want to process (or '0' for ALL PATHS): ").strip())
                    if 0 <= choice < len(path_options):
                        if choice == 0:
                            selected_path = "ALL" 
                        else:
                            selected_path = paths_in_folder[choice - 1]
                        print(f"\nYou selected: {path_options[choice][1]}")
                    else:
                        raise ValueError
                except ValueError:
                    print("Invalid selection. Please enter a valid number.")

            if selected_path == "ALL":

                # Process all Paths in the selected Folder
                print("Calculating distance for all Paths...")
                sum_all_distance = sum_calculate_path_distance(paths_in_folder)

            else:
                
                print("Calculating distance for the selected Path...")
                sum_all_distance = calculate_path_distance(selected_path)

    print("Total Distance: " + str(sum_all_distance))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)