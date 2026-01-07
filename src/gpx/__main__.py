"""Entry point for running the package as a script via `python -m gpx`."""

import sys

from .cli import cli

if __name__ == "__main__":
    sys.exit(cli())
