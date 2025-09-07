"""
gpx_to_kml.py

Summary:
Process a .GPX file as a placemark to append into a Google Earth KML file.

Arguments:
    1) [Required] .gpx file path
       Each .gpx file will be transformed into a single placemark in the destination .KML file  
    2) [Required] Destination KML File Path - the destination .KML file to write the .gpx as a placemark
    3) [Optional, prompted if not entered] Name for the placemark
    4) [Optional, prompted if not entered] .KML Folder to put the placemark into 
"""

import sys
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
    return filename  # Return the valid filename

def check_gpx_file(filename):
    return check_file_extension(filename, ".gpx")

def check_kml_file(filename):
    return check_file_extension(filename, ".kml")

# Handle Arguments
parser = argparse.ArgumentParser(description="Process a GPX file as a placemark to append into a KML file.")

parser.add_argument("-i", "--gpx", type=check_gpx_file, required=True, help="Input (.gpx) file path")
parser.add_argument("-o", "--kml", type=check_kml_file, required=True, help="Output (.kml) file path")
parser.add_argument("-p", "--placemark", type=str, help="Name of the placemark that the .gpx will be turned into")
parser.add_argument("-f", "--folder", type=str, help="Folder to put the placemark into")

args = parser.parse_args()

if not args.placemark:
    args.placemark = input("Please enter a name for the Placemark: ")

# Parse the GPX file
tree = etree.parse(args.gpx)
root = tree.getroot()

# Build the Placemark XML
kml_placemark = f"""\
<Placemark>
    <name>{args.placemark}</name>
    <visibility>0</visibility>
    <styleUrl>#inline</styleUrl>
    <LineString>
        <tessellate>1</tessellate>
        <coordinates>"""

for trkpt in root.xpath("//gpx:trkpt", namespaces=ns):

    kml_placemark = kml_placemark + trkpt.get("lon") + "," + trkpt.get("lat") + ",0 "
    
kml_placemark = kml_placemark + """</coordinates> </LineString> </Placemark>"""

placemark_element = etree.XML(kml_placemark)
etree.indent(placemark_element)

# Parse the KML file
tree = etree.parse(args.kml)
root = tree.getroot()

my_places_folder = root.find(".//kml:Folder[kml:name='My Places']", ns)

subfolders = my_places_folder.findall("kml:Folder", ns)

# Create a list of folder names
folder_options = []
for index, subfolder in enumerate(subfolders):
    name_element = subfolder.find("kml:name", ns)
    folder_name = name_element.text if name_element is not None else f"Unnamed Folder {index}"
    folder_options.append((index, folder_name))

# Prompt user to select a folder
selected_folder = None

if not args.folder:
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

selected_folder.append(placemark_element)

# Write back with pretty-printing
with open(args.kml, "wb") as f:
    f.write(etree.tostring(tree, pretty_print=True, encoding="utf-8", xml_declaration=True))

print("Placemark successfully added to the KML file.")