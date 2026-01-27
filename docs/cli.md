# CLI Reference

The `gpx` command-line interface (CLI) provides tools for validating, inspecting, editing, merging, and converting GPX files. This page shows the `--help` for the `gpx` CLI and all of its sub-commands.

<!--[[[cog
import subprocess

import cog


def help_output(args):
    """Run gpx CLI with args and output formatted help."""
    result = subprocess.run(
        ["gpx"] + args,
        capture_output=True,
        text=True,
    )
    output = result.stdout or result.stderr
    cog.out(f"\nRunning `gpx {' '.join(args)}` or `python -m gpx {' '.join(args)}` shows a list of all of the available options and arguments:\n")
    cog.out(f"\n```shell\n{output}```\n\n")
cog.outl()
]]]-->

<!--[[[end]]]-->

## gpx

<!--[[[cog
help_output(["--help"])
]]]-->

Running `gpx --help` or `python -m gpx --help` shows a list of all of the available options and arguments:

```shell
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
    convert             Convert between GPX, GeoJSON, and KML file formats
```

<!--[[[end]]]-->

## gpx validate

Validate one or more GPX files for well-formedness and basic structure.

<!--[[[cog
help_output(["validate", "--help"])
]]]-->

Running `gpx validate --help` or `python -m gpx validate --help` shows a list of all of the available options and arguments:

```shell
usage: gpx validate [-h] <INPUT_FILE>

Validate a GPX file by attempting to parse it.

positional arguments:
  <INPUT_FILE>  Path to the input GPX file

options:
  -h, --help    show this help message and exit
```

<!--[[[end]]]-->

## gpx info

Display information and statistics about a GPX file.

<!--[[[cog
help_output(["info", "--help"])
]]]-->

Running `gpx info --help` or `python -m gpx info --help` shows a list of all of the available options and arguments:

```shell
usage: gpx info [-h] [--json] <INPUT_FILE>

Display detailed information and statistics about a GPX file.

positional arguments:
  <INPUT_FILE>  Path to the input GPX file

options:
  -h, --help    show this help message and exit
  --json        Output information in JSON format
```

<!--[[[end]]]-->

## gpx edit

Edit a GPX file with various transformations.

<!--[[[cog
help_output(["edit", "--help"])
]]]-->

Running `gpx edit --help` or `python -m gpx edit --help` shows a list of all of the available options and arguments:

```shell
usage: gpx edit [-h] -o <OUTPUT_FILE> [--min-lat LATITUDE]
                [--max-lat LATITUDE] [--min-lon LONGITUDE]
                [--max-lon LONGITUDE] [--start DATETIME] [--end DATETIME]
                [--reverse] [--reverse-routes] [--reverse-tracks]
                [--strip-name] [--strip-desc] [--strip-author]
                [--strip-copyright] [--strip-time] [--strip-keywords]
                [--strip-links] [--strip-all-metadata] [--precision DIGITS]
                [--elevation-precision DIGITS]
                <INPUT_FILE>

Edit a GPX file with various transformations like cropping, trimming,
reversing, and stripping metadata.

positional arguments:
  <INPUT_FILE>          Path to the input GPX file

options:
  -h, --help            show this help message and exit
  -o, --output-file <OUTPUT_FILE>
                        Path to the output file

crop options:
  Crop to a geographic bounding box

  --min-lat LATITUDE    Minimum latitude for crop
  --max-lat LATITUDE    Maximum latitude for crop
  --min-lon LONGITUDE   Minimum longitude for crop
  --max-lon LONGITUDE   Maximum longitude for crop

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

Running `gpx merge --help` or `python -m gpx merge --help` shows a list of all of the available options and arguments:

```shell
usage: gpx merge [-h] -o <OUTPUT_FILE> <INPUT_FILE> [<INPUT_FILE> ...]

Merge multiple GPX files into a single GPX file.

positional arguments:
  <INPUT_FILE>          Paths to the GPX files to merge

options:
  -h, --help            show this help message and exit
  -o, --output-file <OUTPUT_FILE>
                        Path to the output file
```

<!--[[[end]]]-->

## gpx convert

Convert between GPX, GeoJSON, and KML formats.

<!--[[[cog
help_output(["convert", "--help"])
]]]-->

Running `gpx convert --help` or `python -m gpx convert --help` shows a list of all of the available options and arguments:

```shell
usage: gpx convert [-h] -o <OUTPUT_FILE> [-f {gpx,geojson,kml}]
                   [-t {gpx,geojson,kml}]
                   <INPUT_FILE>

Convert GPX files to other file formats or vice versa.

positional arguments:
  <INPUT_FILE>          Path to the input file

options:
  -h, --help            show this help message and exit
  -o, --output-file <OUTPUT_FILE>
                        Path to the output file
  -f, --from-format {gpx,geojson,kml}
                        Input format (default: auto-detect from file
                        extension)
  -t, --to-format {gpx,geojson,kml}
                        Output format (default: auto-detect from file
                        extension)
```

<!--[[[end]]]-->
