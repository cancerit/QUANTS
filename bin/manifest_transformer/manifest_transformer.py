#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a Python 3.8 dropin script for QUANTS that transfroms CSV/TSV manifest files.

See README.md for more information.
"""
import sys
from src.args import get_argparser, CleanArgs
from src import exceptions as exc
from src import cli
from src import summary


def safe_main(clean_args: CleanArgs):
    """Main function."""
    try:
        main(clean_args)
    except (exc.ValidationError, exc.UserInterventionRequired) as err:
        cli.display_error(err, "Error: Argument validation! ")
        sys.exit(1)
    except exc.UndevelopedFeatureError as err:
        cli.display_error(err, "Error: Not implemented feature! ")
        sys.exit(1)


def main(clean_args: CleanArgs):
    """Main function."""


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        cli.display_error("Python 3.8 or newer is required.")
        sys.exit(1)
    argparser = get_argparser()
    namespace = argparser.parse_args()
    clean_args = CleanArgs.from_namespace(namespace)
    summary.write_summary(
        clean_args.summary_file,
        input_file=clean_args.input_file,
        output_file=clean_args.output_file,
        maybe_json_params_file=namespace.input,
    )
    safe_main(clean_args)
    sys.exit(0)
