# CLI Reference

The `gpx` command-line interface provides tools for validating, inspecting, editing, merging, and converting GPX files.

<!--[[[cog
import cog
import subprocess
import textwrap

def help_output(args):
    """Run gpx CLI with args and output formatted help."""
    result = subprocess.run(
        ["gpx"] + args,
        capture_output=True,
        text=True,
    )
    output = result.stdout or result.stderr
    cog.out("\n```\n")
    cog.out(output)
    cog.out("```\n")
]]]-->
<!--[[[end]]]-->

## gpx

<!--[[[cog
help_output(["--help"])
]]]-->

```
usage: gpx [-h] [--version] {validate,info,edit,merge,convert} ...

A command-line tool for working with GPX files.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

commands:
  Available commands

  {validate,info,edit,merge,convert}
    validate            Validate a GPX file
    info                Show information and statistics about a GPX file
    edit                Edit a GPX file with various transformations
    merge               Merge multiple GPX files into one
    convert             Convert between GPX, GeoJSON, and KML formats
```
<!--[[[end]]]-->

## gpx validate

Validate one or more GPX files for well-formedness and basic structure.

<!--[[[cog
help_output(["validate", "--help"])
]]]-->

```
usage: gpx validate [-h] file

Validate a GPX file by attempting to parse it.

positional arguments:
  file        Path to the GPX file to validate

options:
  -h, --help  show this help message and exit
```
<!--[[[end]]]-->

## gpx info

Display information and statistics about a GPX file.

<!--[[[cog
help_output(["info", "--help"])
]]]-->

```
usage: gpx info [-h] [--json] file

Display detailed information and statistics about a GPX file.

positional arguments:
  file        Path to the GPX file

options:
  -h, --help  show this help message and exit
  --json      Output information in JSON format
```
<!--[[[end]]]-->

## gpx edit

Edit a GPX file with various transformations.

<!--[[[cog
help_output(["edit", "--help"])
]]]-->

```
usage: gpx edit [-h] [-o OUTPUT] [--min-lat LAT] [--max-lat LAT]
                [--min-lon LON] [--max-lon LON] [--start DATETIME]
                [--end DATETIME] [--reverse] [--reverse-routes]
                [--reverse-tracks] [--strip-name] [--strip-desc]
                [--strip-author] [--strip-copyright] [--strip-time]
                [--strip-keywords] [--strip-links] [--strip-all-metadata]
                [--precision DIGITS] [--elevation-precision DIGITS]
                input

Edit a GPX file with various transformations like cropping, trimming,
reversing, and stripping metadata.

positional arguments:
  input                 Path to the input GPX file

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path to the output file (default: overwrite input)

crop options:
  Crop to a geographic bounding box

  --min-lat LAT         Minimum latitude for crop
  --max-lat LAT         Maximum latitude for crop
  --min-lon LON         Minimum longitude for crop
  --max-lon LON         Maximum longitude for crop

trim options:
  Trim to a date/time range

  --start DATETIME      Start datetime (ISO 8601 format, e.g.,
                        2024-01-01T10:00:00)
  --end DATETIME        End datetime (ISO 8601 format, e.g.,
                        2024-01-01T12:00:00)

reverse options:
  Reverse routes and/or tracks

  --reverse             Reverse all routes and tracks
  --reverse-routes      Reverse only routes
  --reverse-tracks      Reverse only tracks

strip options:
  Strip metadata fields

  --strip-name          Strip metadata name
  --strip-desc          Strip metadata description
  --strip-author        Strip metadata author
  --strip-copyright     Strip metadata copyright
  --strip-time          Strip metadata time
  --strip-keywords      Strip metadata keywords
  --strip-links         Strip metadata links
  --strip-all-metadata  Strip all metadata

precision options:
  Reduce coordinate precision

  --precision DIGITS    Number of decimal places for lat/lon coordinates
                        (e.g., 6)
  --elevation-precision DIGITS
                        Number of decimal places for elevation (e.g., 1)
```
<!--[[[end]]]-->

## gpx merge

Merge multiple GPX files into a single file.

<!--[[[cog
help_output(["merge", "--help"])
]]]-->

```
usage: gpx merge [-h] -o OUTPUT [--creator CREATOR] files [files ...]

Merge multiple GPX files into a single GPX file.

positional arguments:
  files                 Paths to the GPX files to merge

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path to the output GPX file
  --creator CREATOR     Creator string for the merged file (default: gpx-cli)
```
<!--[[[end]]]-->

## gpx convert

Convert between GPX, GeoJSON, and KML formats.

<!--[[[cog
help_output(["convert", "--help"])
]]]-->

```
usage: gpx convert [-h] -o OUTPUT [-f {gpx,geojson,kml}]
                   [-t {gpx,geojson,kml}]
                   input

Convert GPX files to other formats or vice versa.

positional arguments:
  input                 Path to the input file

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path to the output file
  -f {gpx,geojson,kml}, --from-format {gpx,geojson,kml}
                        Input format (default: auto-detect from extension)
  -t {gpx,geojson,kml}, --to-format {gpx,geojson,kml}
                        Output format (default: auto-detect from extension)
```
<!--[[[end]]]-->
