"""
googleEarth_util.py

Summary:
    Contains utilities shared by the Google Earth Python scripts.

"""

import os
import argparse
from lxml import etree

ns = {"kml": "http://www.opengis.net/kml/2.2",
      "gpx": "http://www.topografix.com/GPX/1/1"}

def check_file_extension(filename, extension):
    if not filename.lower().endswith(extension):
        raise argparse.ArgumentTypeError(f"Invalid file type: Only {extension} files are allowed.")
    if not os.path.isfile(filename):
        raise argparse.ArgumentTypeError(f"File '{filename}' does not exist.")
    return filename

def check_gpx_file(filename):
    return check_file_extension(filename, ".gpx")

def check_kml_file(filename):
    return check_file_extension(filename, ".kml")

def kml_find_folder(root_folder, path):
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

def kml_folder_name(folder):
    name_element = folder.find("kml:name", ns)
    if name_element is not None and name_element.text:
        return name_element.text.strip()
    else:
        return "Unnamed Folder"

# Simple version of kml_prompt_user_selected_folder 
def kml_prompt_user_selected_folder(starting_folder):
    
    current_folder = starting_folder
    
    while True:

        subfolders = current_folder.findall("kml:Folder", ns)

        if not subfolders:
            return current_folder

        # Create a list of folder names
        print("\nCurrent Folder: " + kml_folder_name(current_folder))
        folder_options = []

        for index, subfolder in enumerate(subfolders):
            folder_options.append((index + 1, kml_folder_name(subfolder)))

        selected_folder = None
        while selected_folder is None:
            print("")
            for idx, name in folder_options:
                print(f"{idx}. {name}")

            try:

                choice = int(input("\nSelect a folder: ").strip())

                if 1 <= choice <= len(folder_options):
                    selected_folder = subfolders[choice - 1]
                    print(f"\nYou selected: {folder_options[choice - 1][1]}\n")
                else:
                    raise ValueError
                    
            except ValueError:
                print("Invalid selection. Please enter a valid number.")

        current_folder = selected_folder