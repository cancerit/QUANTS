import typing as t
import argparse
from pathlib import Path
from dataclasses import dataclass

from src import constants as const
from src import version
from src import exceptions


@dataclass
class ParsedColumns:
    column_order: t.Tuple[str, ...]
    required_columns: t.Tuple[str, ...]
    optional_columns: t.Tuple[str, ...]

    def __post_init__(self):
        iterable = [
            ("column_order", self.column_order),
            ("required_columns", self.required_columns),
            ("optional_columns", self.optional_columns),
        ]
        for attr, value in iterable:
            for element in value:
                if not isinstance(element, (str, int)):
                    msg = f"{attr} must be a tuple of strings (or ints which are converted to str), but {element} is a {type(element)}"
                    raise TypeError(msg)
            # Normalise all elements to strings
            setattr(self, attr, tuple([str(element) for element in value]))
        return

    def assert_valid(self):
        """
        Assert the columns are valid.

        Checks that:
        1. There are no duplicate columns
        2. The column_order columns are only from required_columns and optional_columns
        3. The required_columns and optional_columns are disjoint (no overlap)
        4. There are no labels in the columns
        """
        callables = [
            self._assert_no_duplicates,
            self._assert_column_order_valid,
            self._assert_required_optional_disjoint,
            self._assert_no_labels_in_column,
        ]
        for callable_ in callables:
            callable_()

    def _assert_no_duplicates(self):
        """
        Assert there are no duplicate columns.
        """
        column_containers = {
            "required columns": self.required_columns,
            "optional columns": self.optional_columns,
            "column order": self.column_order,
        }
        for name, column_container in column_containers.items():
            if len(column_container) != len(set(column_container)):
                msg = f"Duplicate columns found in {name}: {column_container}"
                raise exceptions.ValidationError(msg)

    def _assert_column_order_valid(self):
        """
        Assert the column_order columns are consist of columns only in required
        columns and optional columns.
        """
        order = set(self.column_order)
        required = set(self.required_columns)
        optional = set(self.optional_columns)
        is_valid = set(order) == set(required) | set(optional)
        if not is_valid:
            not_subset_columns = order - (required | optional)
            detail = ", ".join(not_subset_columns)
            msg = (
                "Column order columns must be a subset of required columns and optional columns, "
                f"but the following columns were not found in either: {detail}"
            )
            raise exceptions.ValidationError(msg)

    def _assert_required_optional_disjoint(self):
        """
        Assert the required_columns and optional_columns are disjoint (no overlap).
        """
        required = set(self.required_columns)
        optional = set(self.optional_columns)
        is_valid = required.isdisjoint(optional)
        if not is_valid:
            detail = ", ".join(required & optional)
            msg = (
                "Required columns and optional columns must not overlap, "
                f"but the following columns were found in both: {detail}"
            )
            raise exceptions.ValidationError(msg)

    def _assert_no_labels_in_column(self):
        """
        Assert there are no labels in the columns.
        """
        required_label = const.ARGPREFIX__REQUIRED_COLUMN
        optional_label = const.ARGPREFIX__OPTIONAL_COLUMN
        for column in self.column_order:
            has_required_label = column.startswith(required_label)
            has_optional_label = column.startswith(optional_label)
            if has_required_label or has_optional_label:
                msg = (
                    f"Encountered a labelled column name: {column!r}, "
                    f"but all column names must be unlabelled."
                )
                raise exceptions.ValidationError(msg)

    def is_valid(self) -> bool:
        """
        Checks if the columns are valid.

        Checks that:
        1. There are no duplicate columns
        2. The column_order columns are only from required_columns and optional_columns
        3. The required_columns and optional_columns are disjoint (no overlap)
        4. There are no labels in the columns
        """
        try:
            self.assert_valid()
        except exceptions.ValidationError:
            return False
        else:
            return True

    @classmethod
    def from_labelled_columns(
        cls, labelled_columns: t.Iterable[str]
    ) -> "ParsedColumns":
        """
        Create a ParsedColumns object from a list of labelled columns, typically from the argparser namespace.
        """
        column_order = []
        required_columns = []
        optional_columns = []
        label_required = const.ARGPREFIX__REQUIRED_COLUMN
        label_optional = const.ARGPREFIX__OPTIONAL_COLUMN
        for labelled_column in labelled_columns:
            is_required = labelled_column.startswith(label_required)
            is_optional = labelled_column.startswith(label_optional)
            if is_required:
                column = labelled_column.replace(label_required, "", 1)
                required_columns.append(column)
            elif is_optional:
                column = labelled_column.replace(label_optional, "", 1)
                optional_columns.append(column)
            else:
                msg = (
                    f"Encountered an unlabelled column name: {labelled_column!r}, "
                    f"but all column names must be labelled with either {label_required!r} "
                    f"or {label_optional!r}."
                )
                raise ValueError(msg)
            column_order.append(column)

        obj = cls(
            tuple(column_order),
            tuple(required_columns),
            tuple(optional_columns),
        )
        return obj


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
        metavar="SUBCOMMAND",
        required=True,
    )
    subparser_cli_col_names = subparsers.add_parser(
        const.SUBCOMMAND__COLUMN_NAMES,
        description=const.HELP__PROG_DESCRIPTION,
        help="Execution from command line arguments (specifing column names).",
    )
    subparser_cli_col_indices = subparsers.add_parser(
        const.SUBCOMMAND__COLUMN_INDICES,
        description=const.HELP__PROG_DESCRIPTION,
        help="Execution from command line arguments (specifing column indices).",
    )
    subparser_json = subparsers.add_parser(
        const.SUBCOMMAND__JSON,
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
    parser.add_argument(
        const.ARG_OUTPUT,
        type=Path,
        help=const.HELP__OUTPUT_FILE,
        metavar="OUTPUT",
    )
    # Required columns
    required_columns_help = (
        const.HELP__REQUIRED_COLUMNS_BY_NAME
        if use_name
        else const.HELP__REQUIRED_COLUMNS_BY_INDEX
    )
    parser.add_argument(
        "--output-as-tsv",
        action="store_const",
        const=const.DELIMITER__TAB,
        default=const.DELIMITER__COMMA,
        help=const.HELP__CAST_OUTPUT_AS_TSV,
        dest=const.ARG_OUTPUT_DELIMITER,
    )
    parser.add_argument(
        "-s",
        "--summary",
        type=Path,
        default=None,
        help=const.HELP__SUMMARY_FILE,
        dest=const.ARG_SUMMARY,
        metavar="SUMMARY",
    )

    # Required columns
    parser.add_argument(
        "-c",
        "--columns",
        nargs="+",
        default=None,
        action="extend",
        type=lambda x: _label_required_column(x),
        help=required_columns_help,
        dest=const.ARG_COLUMNS,
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
        type=lambda x: _label_optional_column(x),
        default=None,
        action="extend",
        help=optional_columns_help,
        dest=const.ARG_COLUMNS,
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

    # Reheader append or replace
    parser.add_argument(
        "--reheader-append",
        action="store_true",
        default=False,
        help=const.HELP__REHEADER_APPEND,
        dest=const.ARG_REHEADER_APPEND,
    )

    # Forced delimiter argument mutually exclusive group (only one can be used) for comma and tab
    forced_delimiter_group = parser.add_mutually_exclusive_group(required=False)
    forced_delimiter_group.add_argument(
        "--force-comma",
        action="store_const",
        const=const.DELIMITER__COMMA,
        default=None,
        help=const.HELP__FORCE_COMMA_DELIMITER,
        dest=const.ARG_FORCE_INPUT_DELIMITER,
    )
    forced_delimiter_group.add_argument(
        "--force-tab",
        action="store_const",
        const=const.DELIMITER__TAB,
        default=None,
        help=const.HELP__FORCE_TAB_DELIMITER,
        dest=const.ARG_FORCE_INPUT_DELIMITER,
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


def _label_required_column(
    column: t.Union[str, int],
) -> str:
    column_str = str(column)
    return _prefix_column(column_str, const.ARGPREFIX__REQUIRED_COLUMN)


def _label_optional_column(
    column: t.Union[str, int],
) -> str:
    column_str = str(column)
    return _prefix_column(column_str, const.ARGPREFIX__OPTIONAL_COLUMN)


def _prefix_column(column: str, prefix: str) -> str:
    return f"{prefix}{str(column)}"


def parse_reheader_columns(columns: t.Optional[t.List[str]]) -> t.Dict[str, str]:
    """
    Parses a list of strings of the format ["col1=COL1", "col2=COL2"]
    into a dictionary like {"col1": "COL1", "col2": "COL2"}

    If columns is None, returns an empty dictionary.

    Args:
        columns: A list of strings formatted as "column_name=mapped_column_name"

    Returns:
        A dictionary where key is column_name and value is mapped_column_name
    """
    if columns is None:
        return {}
    seperator = "="
    mappings = {}
    for column in columns:
        parts = column.split(seperator, 1)
        if len(parts) != 2:
            msg = f"Invalid reheader column syntax: {column!r}, must be of the form 'column_name=mapped_column_name'. All reheader columns: {columns}."
            raise exceptions.ValidationError(msg)
        column_name, mapped_name = parts
        mappings[column_name] = mapped_name
    return mappings


def parse_integer_like_list(integer_list: t.List[str]) -> t.List[int]:
    """
    Parses a list of strings of the format ["1", "2", "3"] into a list of
    integers [1, 2, 3]
    """
    parsed_list = []
    for integer_like in integer_list:
        try:
            parsed_list.append(int(integer_like))
        except ValueError:
            msg = f"Column does not resemble an index, as it is not an integer-like value: {integer_like}"
            raise exceptions.ValidationError(msg) from None
    return parsed_list


def parse_integer_like_dict(integer_dict: t.Dict[str, str]) -> t.Dict[int, str]:
    """
    Parses a dictionary of strings of the format {"1": "col1", "2": "col2", "3":
    "col3"} into a dictionary of integers {1: "col1", 2: "col2", 3: "col3"}
    """
    parsed_dict = {}
    for key, value in integer_dict.items():
        try:
            parsed_dict[int(key)] = value
        except ValueError:
            msg = f"Column does not resemble an index, as it is not an integer-like value: {key}"
            raise exceptions.ValidationError(msg) from None
    return parsed_dict
