import argparse
from pathlib import Path

from src import constants as const
from src import version


def get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=const.HELP__PROG_DESCRIPTION)
    # Version
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version.VERSION}",
        help=const.HELP__VERSION,
    )

    # Add subparsers
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="valid subcommands",
        dest=const.ARG_SUBCOMMAND,
        required=False,
    )
    subparser_cli_col_names = subparsers.add_parser(
        "column-names",
        description=const.HELP__PROG_DESCRIPTION,
        help="Execution from command line arguments (specifing column names).",
    )
    subparser_cli_col_indices = subparsers.add_parser(
        "column-indices",
        description=const.HELP__PROG_DESCRIPTION,
        help="Execution from command line arguments (specifing column indices).",
    )
    subparser_json = subparsers.add_parser(
        "json",
        description=const.HELP__PROG_DESCRIPTION,
        help="Execution from a JSON parameter file instead of command line arguments.",
    )

    # JSON subparser
    subparser_json.add_argument(
        const.ARG_INPUT,
        type=Path,
        help=const.HELP__JSON_INPUT_FILE,
    )

    # CLI parsers
    _add_common_arguments_to_parser(subparser_cli_col_names, use_name=True)
    _add_common_arguments_to_parser(subparser_cli_col_indices, use_name=False)
    return parser


def _add_common_arguments_to_parser(parser, use_name: bool):
    iterable_metavar = "NAME" if use_name else "INDEX"
    parser.add_argument(
        const.ARG_INPUT,
        type=Path,
        help=const.HELP__INPUT_FILE,
        metavar="INPUT",
    )
    # Required columns
    required_columns_help = (
        const.HELP__REQUIRED_COLUMNS_BY_NAME
        if use_name
        else const.HELP__REQUIRED_COLUMNS_BY_INDEX
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=const.HELP__OUTPUT_FILE,
        dest=const.ARG_OUTPUT,
        metavar="OUTPUT",
    )
    # Required columns
    parser.add_argument(
        "-c",
        "--columns",
        nargs="+",
        default=None,
        help=required_columns_help,
        dest=const.ARG_REQUIRED_COLUMNS,
        metavar=iterable_metavar,
        required=True,
    )

    # Optional columns
    optional_columns_help = (
        const.HELP__OPTIONAL_COLUMNS_BY_NAME
        if use_name
        else const.HELP__OPTIONAL_COLUMNS_BY_INDEX
    )
    parser.add_argument(
        "-C",
        "--optional-columns",
        nargs="+",
        default=None,
        help=optional_columns_help,
        dest=const.ARG_OPTIONAL_COLUMNS,
        metavar=iterable_metavar,
    )
    # Reheader
    reheader_help = (
        const.HELP__REHEADER_BY_NAME if use_name else const.HELP__REHEADER_BY_INDEX
    )
    reheader_metavar = "NAME=NEW_NAME" if use_name else "INDEX=NEW_NAME"
    parser.add_argument(
        "-r",
        "--reheader",
        nargs="+",
        default=None,
        help=reheader_help,
        dest=const.ARG_REHEADER,
        metavar=reheader_metavar,
    )

    # Forced delimiter argument mutually exclusive group (only one can be used) for comma and tab

    forced_delimiter_group = parser.add_mutually_exclusive_group(required=False)
    forced_delimiter_group.add_argument(
        "--force-comma",
        action="store_const",
        const=",",
        default=None,
        help=const.HELP__FORCE_COMMA_DELIMITER,
        dest=const.ARG_FORCE_DELIMITER,
    )
    forced_delimiter_group.add_argument(
        "--force-tab",
        action="store_const",
        const="\t",
        default=None,
        help=const.HELP__FORCE_TAB_DELIMITER,
        dest=const.ARG_FORCE_DELIMITER,
    )

    # Forced column header line index
    parser.add_argument(
        "--force-header-row-index",
        type=int,
        default=None,
        help=const.HELP__FORCE_HEADER_ROW_INDEX,
        dest=const.ARG_FORCE_HEADER_ROW_INDEX,
        metavar="INDEX",
    )
    return
