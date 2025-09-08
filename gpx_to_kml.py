"""
gpx_to_kml.py

Summary:
    Converts a single .GPX file into a Google Earth Path and appends to the destination Google Earth .KML file.

Arguments:
    1) [Required] -i: Input (.GPX) file path.
    2) [Required] -o: Output (.KML) file path.
    3) [Optional] -p: Name of the Path that the .GPX will be converted into.
    4) [Optional] -f: Folder path within the .KML file to put the new Path into.

"""

import sys
import googleEarth_util as util

def main():

    # Handle Arguments
    parser = util.argparse.ArgumentParser(description="Converts a single .GPX file into a Google Earth Path and appends to the destination Google Earth .KML file.")

    parser.add_argument("-i", "--gpx", type=util.check_gpx_file, required=True, help="Input (.GPX) file path.")
    parser.add_argument("-o", "--kml", type=util.check_kml_file, required=True, help="Output (.KML) file path.")
    parser.add_argument("-p", "--path", type=str, help="Name of the Path that the .GPX will be converted into.")
    parser.add_argument("-f", "--folder", type=str, help="Folder path within the .KML file to put the new Path into.")
    args = parser.parse_args()

    while not args.path:
        args.path = input("Please enter a name for the new Path: ").strip()

    # Parse the .GPX file
    gpx_tree = util.etree.parse(args.gpx)
    gpx_root = gpx_tree.getroot()

    # Build the .GPX Path Placemark XML
    gpx_placemark = f"""\
        <Placemark>
            <name>{args.path}</name>
            <visibility>0</visibility>
            <styleUrl>#inline</styleUrl>
            <LineString>
                <tessellate>1</tessellate>
                <coordinates>"""

    for trkpt in gpx_root.xpath("//gpx:trkpt", namespaces=util.ns):

        gpx_placemark = gpx_placemark + trkpt.get("lon") + "," + trkpt.get("lat") + ",0 "
        
    gpx_placemark = gpx_placemark + """</coordinates> </LineString> </Placemark>"""

    gpx_placemark_element = util.etree.XML(gpx_placemark)
    util.etree.indent(gpx_placemark_element)

    # Parse the KML file
    kml_tree = util.etree.parse(args.kml)
    kml_root = kml_tree.getroot()
    top_folder = kml_root.find(".//kml:Folder", util.ns)

    # Folder Selection
    selected_folder = None

    if args.folder:

        # Use the Folder path passed in as the argument
        selected_folder = util.kml_find_folder(top_folder, args.folder)

        if selected_folder is None:
            print("Error: The folder indicated in arguments was not found within the .KML. Exiting...")
            sys.exit(1)

    else:
        
        # Prompt user to select a Folder
        selected_folder = util.kml_prompt_user_selected_folder(top_folder)

    # Append the Path Placemark with pretty-printing
    selected_folder.append(gpx_placemark_element)

    with open(args.kml, "wb") as f:
        f.write(util.etree.tostring(kml_tree, pretty_print=True, encoding="utf-8", xml_declaration=True))

    print("Path successfully added to the .KML file!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)