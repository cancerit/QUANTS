import argparse
from pathlib import Path

from src import constants as const


def get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transforms oligo sequences to a format that can be used in PyQuest"
    )
    # File arguments
    parser.add_argument(
        const._ARG_INPUT,
        type=Path,
        help=const._HELP__INPUT_FILE,
        metavar="INPUT",
    )
    parser.add_argument(
        const._ARG_OUTPUT,
        type=Path,
        default=None,
        help=const._HELP__OUTPUT_FILE,
        metavar="OUTPUT",
    )

    # Verbosity
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help=const._HELP__VERBOSE,
        dest=const._ARG_VERBOSE,
    )

    # DNA primer arguments (forward and reverse primers while we don't consider 5 and 3 prime ends or reverse complement complexity)
    parser.add_argument(
        "--forward",
        type=str,
        default="",
        help=const._HELP__FORWARD_PRIMER,
        dest=const._ARG_FORWARD_PRIMER,
    )
    parser.add_argument(
        "--reverse",
        type=str,
        default="",
        help=const._HELP__REVERSE_PRIMER,
        dest=const._ARG_REVERSE_PRIMER,
    )

    # Include a way to skip N rows of the input file
    parser.add_argument(
        "--skip",
        type=int,
        default=1,
        help=const._HELP__SKIP_N_ROWS,
        dest=const._ARG_SKIP_N_ROWS,
    )

    # Include a way to toggle the output sequences to be in reverse complement, default is false
    parser.add_argument(
        "--revcomp",
        action="store_true",
        default=False,
        help=const._HELP__REVERSE_COMPLEMENT_FLAG,
        dest=const._ARG_REVERSE_COMPLEMENT_FLAG,
    )

    # Mutually exclusive argument group for oligo sequence name
    name_group = parser.add_mutually_exclusive_group(required=True)
    name_group.add_argument(
        "-n",
        "--name-header",
        type=str,
        help=const._HELP__GROUP_NAME,
        dest=const._ARG_NAME_HEADER,
    )
    name_group.add_argument(
        "-N",
        "--name-index",
        type=int,
        help=const._HELP__GROUP_NAME_IDX,
        dest=const._ARG_NAME_INDEX,
    )

    # Mutually exclusive argument group for oligo sequence
    sequence_group = parser.add_mutually_exclusive_group(required=True)
    sequence_group.add_argument(
        "-s",
        "--sequence-header",
        type=str,
        help=const._HELP__GROUP_SEQ,
        dest=const._ARG_SEQ_HEADER,
    )
    sequence_group.add_argument(
        "-S",
        "--sequence-index",
        type=int,
        help=const._HELP__GROUP_SEQ_IDX,
        dest=const._ARG_SEQ_INDEX,
    )
    return parser
