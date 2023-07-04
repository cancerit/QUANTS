#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a Python 3.8 dropin script for QUANTS that transfroms CSV/TSV manifest files.

See README.md for more information.
"""
import sys
from src import constants as const
from src import exceptions as exc
from src import cli


def main():
    """Main function."""
    print("Hello World!", const.VERSION)


if __name__ == "__main__":
    try:
        main()
    except exc.ValidationError as err:
        cli.display_error(err, "Error: Argument validation! ")
        sys.exit(1)
    except exc.UndevelopedFeatureError as err:
        cli.display_error(err, "Error: Not implemented feature! ")
        sys.exit(1)
    sys.exit(0)
