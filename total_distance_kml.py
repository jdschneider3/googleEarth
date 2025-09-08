"""
total_distance_kml.py

Summary:
    For the given .KML file, a total distance in miles is returned based on optional parameters/prompts.

Arguments:
    1) [Required] -i: Input (.KML) file path.
    2) [Optional] -f: Folder path within the .KML file to calculate distance on.
    3) [Optional] -p: Name of the Path inside of the specified Folder to calculate distance on.
    4) [Optional] -r: Recursive Mode - Calculate distance on all Paths within the specified Folder + Sub-Folders.

Notes:
    Default File Path to Google Earth myplaces.kml is in regedit: HKEY_CURRENT_USER\Software\Google\Google Earth Pro\KMLPath.

"""

import sys
import googleEarth_util as util
from geopy.distance import geodesic

def calculate_path_distance(path):
    path_coordinates = path.find(".//kml:coordinates", util.ns)
    
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

# "Total Distance"-specific version of kml_prompt_user_selected_folder
def kml_prompt_user_selected_folder(starting_folder):
    recursive_folder_mode = False
    current_folder = starting_folder
    
    while True:

        numPaths = len(current_folder.findall("kml:Placemark[kml:LineString]", util.ns))
        subfolders = current_folder.findall("kml:Folder", util.ns)

        if not subfolders:
            return current_folder, recursive_folder_mode

        # Create a list of folder names
        print("\nCurrent Folder: " + util.kml_folder_name(current_folder) + " ( " + str(numPaths) + " Path(s) )")
        folder_options = [(0, "<Current Folder>")]

        for index, subfolder in enumerate(subfolders):
            folder_options.append((index + 1, util.kml_folder_name(subfolder)))

        selected_folder = None
        while selected_folder is None:
            print("")
            for idx, name in folder_options:
                print(f"{idx}. {name}")

            choice_str = input("\nSelect a folder (+ \"r\" for Recursive Mode): ").strip()
            
            if choice_str.lower().endswith("r"):
                recursive_folder_mode = True
                choice_str = choice_str[:-1]

            try:

                choice = int(choice_str)

                if 0 <= choice < len(folder_options):
                    if choice == 0:
                        return current_folder, recursive_folder_mode
                    else:
                        selected_folder = subfolders[choice - 1]
                        print(f"\nYou selected: {folder_options[choice][1]}{' (Recursive Mode)' if recursive_folder_mode else ''}\n")
                else:
                    raise ValueError
     
                # Exit early if recrusive mode was specified
                if recursive_folder_mode:
                    return selected_folder, recursive_folder_mode
                    
            except ValueError:
                print("Invalid selection. Please enter a valid number (optionally followed by 'r').")

        current_folder = selected_folder

def sum_calculate_path_distance(all_paths):
    sum_distance = 0
    for path in all_paths:
        sum_distance += calculate_path_distance(path)   
    return sum_distance

def main():
    
    sum_all_distance = 0
    selected_recursive = False

    # Handle Arguments
    parser = util.argparse.ArgumentParser(description="For the given .KML file, a total distance in miles is returned based on optional parameters/prompts.")
    
    parser.add_argument("-i", "--kml", type=util.check_kml_file, required=True, help="Input (.KML) file path.")
    parser.add_argument("-f", "--folder", type=str, help="Folder path within the .KML file to calculate distance on.")
    parser.add_argument("-p", "--path", type=str, help="Name of the Path inside of the specified Folder to calculate distance on.")
    parser.add_argument("-r", "--recursive", action="store_true", help="Calculate distance on all Paths within the specified Folder + Sub-Folders.")
    args = parser.parse_args()

    # Validate arguments
    if not args.folder and args.path:
        print("Error: Folder must also be specified, when specifying a Path. Exiting...")
        sys.exit(1)

    # Parse the KML file
    kml_tree = util.etree.parse(args.kml)
    kml_root = kml_tree.getroot()
    top_folder = kml_root.find(".//kml:Folder", util.ns)

    # Folder Selection
    selected_folder = None

    if not args.folder and not args.path and args.recursive :
    
        # Calculate total distance on all Paths within the entire file.
        selected_folder = top_folder

    else:
        
        if args.folder:

            # Use the Folder path passed in as the argument
            selected_folder = util.kml_find_folder(top_folder, args.folder)

            if selected_folder is None:
                print("Error: The folder indicated in arguments was not found within the .KML. Exiting...")
                sys.exit(1)

        else:

            # Prompt user to select a Folder
            selected_folder, selected_recursive = kml_prompt_user_selected_folder(top_folder)
            
    # Path Selection
    selected_path = None

    if args.path:

        # Use the Path Name passed in as the argument
        selected_path = selected_folder.find("kml:Placemark[kml:name='" + args.path + "']", util.ns)
        
        if selected_path is None or selected_path.find("kml:LineString", util.ns) is None:
            print("Error: The Path name indicated in the arguments was not found in the .KML. Exiting...")
            sys.exit(1)
        
        sum_all_distance = calculate_path_distance(selected_path)

    else:

        if args.recursive:

            # Process all Paths in the selected Folder recursively            
            print("Calculating distance for all Paths (Recursive Mode)...")
            sum_all_distance = sum_calculate_path_distance(selected_folder.findall(".//kml:Placemark[kml:LineString]", util.ns))

        else:

            # Prompt user to select a Path
            if selected_recursive:
                paths_in_folder = selected_folder.findall(".//kml:Placemark[kml:LineString]", util.ns)
            else:
                paths_in_folder = selected_folder.findall("kml:Placemark[kml:LineString]", util.ns)

            # Create a list of Path names
            path_options = [(0, "<All Paths>")]
            for index, path in enumerate(paths_in_folder):
                name_element = path.find("kml:name", util.ns)
                path_name = name_element.text if name_element is not None else f"Unnamed Path {index}"
                path_options.append((index + 1, path_name))  # Index starts from 1 for Paths
            
            while selected_path is None:
                print("\nSelect a Path to calculate distance on. Type 0 to calculate distance on ALL Paths: ")

                # Print options for Paths
                for idx, name in path_options:
                    print(f"{idx}. {name}")  # Regular Paths, idx starts from 0 for "All Paths"

                try:
                
                    choice = int(input("\nEnter the number of the path you want to process (or '0' for ALL Paths): ").strip())
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

    print("Total Distance: " + str(sum_all_distance) + " miles.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)