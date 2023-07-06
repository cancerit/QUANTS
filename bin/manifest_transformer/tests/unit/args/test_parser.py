from pathlib import Path

import pytest

from src.args import parser
from src import constants as const


@pytest.mark.parametrize(
    "column_order, required_columns, optional_columns, expected_result",
    [
        # Test case: No duplicate columns, column_order only from required/optional, disjoint required/optional, no labels
        (("col1", "col2", "col3"), ("col1", "col2"), ("col3",), True),
        # Test case: Duplicate columns exist
        (("col1", "col1", "col2"), ("col1", "col2"), ("col3",), False),
        # Test case: column_order columns not only from required/optional
        (("col1", "col2", "col4"), ("col1", "col2"), ("col3",), False),
        # Test case: required_columns and optional_columns not disjoint
        (("col1", "col2", "col3"), ("col1", "col2"), ("col2", "col3"), False),
        # Test case: Labels in the columns
        (
            (
                const.ARGPREFIX__REQUIRED_COLUMN + "col1",
                const.ARGPREFIX__REQUIRED_COLUMN + "col2",
                const.ARGPREFIX__OPTIONAL_COLUMN + "col3",
            ),
            ("col1", "col2"),
            ("col3",),
            False,
        ),
    ],
)
def test_ParsedColumns__is_valid(
    column_order, required_columns, optional_columns, expected_result
):
    # Given
    parsed_columns = parser.ParsedColumns(
        column_order, required_columns, optional_columns
    )

    # When
    actual_result = parsed_columns.is_valid()

    # Then
    assert actual_result == expected_result


def test_ParsedColumns__from_labelled_columns_valid():
    # Given
    labelled_columns = [
        f"{const.ARGPREFIX__REQUIRED_COLUMN}column1",
        f"{const.ARGPREFIX__REQUIRED_COLUMN}column2",
        f"{const.ARGPREFIX__OPTIONAL_COLUMN}column1",
    ]
    expected_column_order = ("column1", "column2", "column1")
    expected_required_columns = ("column1", "column2")
    expected_optional_columns = ("column1",)

    # When
    actual = parser.ParsedColumns.from_labelled_columns(labelled_columns)

    # Then
    assert actual.column_order == expected_column_order
    assert actual.required_columns == expected_required_columns
    assert actual.optional_columns == expected_optional_columns


def test_ParsedColumns__from_labelled_columns_invalid():
    # Given
    labelled_columns = [
        f"{const.ARGPREFIX__REQUIRED_COLUMN}column1",
        f"{const.ARGPREFIX__REQUIRED_COLUMN}column2",
        f"{const.ARGPREFIX__OPTIONAL_COLUMN}column3",
        "column4",  # Unlabelled column
    ]

    # When / Then
    with pytest.raises(ValueError):
        parser.ParsedColumns.from_labelled_columns(labelled_columns)


def test_get_argparser__sub_command__column_names():
    # Given
    cmd = "column-names in.csv -c col1 col2 -C opt-col4 opt-col5 -c col3 -o out.csv -r col1=COL1 col3=COL3"
    expected_input = Path("in.csv")
    expected_output = Path("out.csv")
    expected_output_as_tsv = False
    expected_summary = None
    expected_reheader = ["col1=COL1", "col3=COL3"]
    expected_force_delimiter = None
    expected_force_header_row_index = None

    expected_columns = [
        "REQUIRED_COLUMN:col1",
        "REQUIRED_COLUMN:col2",
        "OPTIONAL_COLUMN:opt-col4",
        "OPTIONAL_COLUMN:opt-col5",
        "REQUIRED_COLUMN:col3",
    ]

    # When
    namespace = parser.get_argparser().parse_args(cmd.split())

    # Then
    assert namespace.subcommand == const.SUBCOMMAND__COLUMN_NAMES
    assert namespace.input == expected_input
    assert namespace.output == expected_output
    assert namespace.cast_output_as_tsv == expected_output_as_tsv
    assert namespace.summary == expected_summary
    assert namespace.reheader == expected_reheader
    assert namespace.force_delimiter == expected_force_delimiter
    assert namespace.force_header_row_index == expected_force_header_row_index
    assert namespace.columns == expected_columns


def test_get_argparser__sub_command__column_indices():
    # Given
    cmd = "column-indices in.csv -c 1 2 -C 4 5 -c 3 -o out.csv -r 1=COL1 3=COL3"
    expected_input = Path("in.csv")
    expected_output = Path("out.csv")
    expected_output_as_tsv = False
    expected_summary = None
    expected_reheader = ["1=COL1", "3=COL3"]
    expected_force_delimiter = None
    expected_force_header_row_index = None

    expected_columns = [
        "REQUIRED_COLUMN:1",
        "REQUIRED_COLUMN:2",
        "OPTIONAL_COLUMN:4",
        "OPTIONAL_COLUMN:5",
        "REQUIRED_COLUMN:3",
    ]

    # When
    namespace = parser.get_argparser().parse_args(cmd.split())

    # Then
    assert namespace.subcommand == const.SUBCOMMAND__COLUMN_INDICES
    assert namespace.input == expected_input
    assert namespace.output == expected_output
    assert namespace.cast_output_as_tsv == expected_output_as_tsv
    assert namespace.summary == expected_summary
    assert namespace.reheader == expected_reheader
    assert namespace.force_delimiter == expected_force_delimiter
    assert namespace.force_header_row_index == expected_force_header_row_index
    assert namespace.columns == expected_columns


def test_get_argparser__sub_command__json():
    # Given
    cmd = "json in.json"
    expected_input = Path("in.json")

    # When
    namespace = parser.get_argparser().parse_args(cmd.split())

    # Then
    assert namespace.subcommand == const.SUBCOMMAND__JSON
    assert namespace.input == expected_input


def test__prefix_column():
    # Given
    column = "col1"
    prefix = const.ARGPREFIX__REQUIRED_COLUMN
    expected = f"{prefix}{column}"

    # When
    actual = parser._prefix_column(column, prefix)

    # Then
    assert actual == expected


def test__label_required_column():
    # Given
    column = "col1"
    expected = f"{const.ARGPREFIX__REQUIRED_COLUMN}{column}"

    # When
    actual = parser._label_required_column(column)

    # Then
    assert actual == expected


def test__label_optional_column():
    # Given
    column = "col1"
    expected = f"{const.ARGPREFIX__OPTIONAL_COLUMN}{column}"

    # When
    actual = parser._label_optional_column(column)

    # Then
    assert actual == expected
