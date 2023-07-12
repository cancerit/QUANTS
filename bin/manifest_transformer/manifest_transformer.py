#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is a Python 3.8 dropin script for QUANTS that transfroms CSV/TSV manifest files.

See README.md for more information.
"""
import typing as t

if t.TYPE_CHECKING:
    from argparse import Namespace

import sys
from src.args import get_argparser, CleanArgs
from src.csv import manifest_transformer, write_output_file
from src import exceptions as exc
from src import cli
from src import summary


def safe_main(namespace: "Namespace"):
    """Main function."""
    try:
        clean_args = CleanArgs.from_namespace(namespace)
        main(clean_args)
    except (exc.ValidationError, exc.UserInterventionRequired) as err:
        cli.display_error(err, "Error: Validation! ")
        sys.exit(1)
    except (exc.UndevelopedFeatureError, NotImplementedError) as err:
        cli.display_error(err, "Error: Not implemented feature! ")
        sys.exit(1)
    except Exception as err:
        cli.display_error(err, "Error: Unhandled error (please report)! ")
        raise


def main(clean_args: CleanArgs):
    """Main function."""

    # Write the summary file
    summary.write_summary(
        clean_args.summary_file,
        input_file=clean_args.input_file,
        output_file=clean_args.output_file,
        maybe_json_params_file=namespace.input_file,
    )
    # Run the main function
    # TODO manifest_validator(clean_args)  # TODO implement manifest_validator - it checks the csv file for errors
    output_io = manifest_transformer(clean_args)

    # Write the output file
    try:
        write_output_file(output_io, clean_args.output_file)
    finally:
        output_io.close()
    return


if __name__ == "__main__":
    if sys.version_info < (3, 8):
        cli.display_error("Python 3.8 or newer is required.")
        sys.exit(1)

    argparser = get_argparser()
    namespace = argparser.parse_args()

    safe_main(namespace)
    sys.exit(0)
