from pathlib import Path

import pytest

from src.args import _parser
from src import constants as const
from src.exceptions import ValidationError


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
    parsed_columns = _parser.ParsedColumns(
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
    actual = _parser.ParsedColumns.from_labelled_columns(labelled_columns)

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
        _parser.ParsedColumns.from_labelled_columns(labelled_columns)


def test_get_argparser__sub_command__column_names():
    # Given
    cmd = "column-names in.csv out.csv -c col1 col2 -C opt-col4 opt-col5 -c col3 -r col1=COL1 col3=COL3 --reheader-append"
    expected_input = Path("in.csv")
    expected_output = Path("out.csv")
    expected_output_delimiter = ","
    expected_summary = None
    expected_reheader = ["col1=COL1", "col3=COL3"]
    expected_reheader_append = True
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
    namespace = _parser.get_argparser().parse_args(cmd.split())

    # Then
    assert namespace.mode == const.SUBCOMMAND__COLUMN_NAMES
    assert namespace.input_file == expected_input
    assert namespace.output_file == expected_output
    assert namespace.output_file_delimiter == expected_output_delimiter
    assert namespace.summary_file == expected_summary
    assert namespace.reheader_mapping == expected_reheader
    assert namespace.reheader_append == expected_reheader_append
    assert namespace.forced_input_file_delimiter == expected_force_delimiter
    assert namespace.forced_header_row_index == expected_force_header_row_index
    assert namespace.columns == expected_columns


def test_get_argparser__sub_command__column_indices():
    # Given
    cmd = "column-indices in.csv out.csv -c 1 2 -C 4 5 -c 3 -r 1=COL1 3=COL3"
    expected_input = Path("in.csv")
    expected_output = Path("out.csv")
    expected_output_delimiter = ","
    expected_summary = None
    expected_reheader = ["1=COL1", "3=COL3"]
    expected_reheader_append = False
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
    namespace = _parser.get_argparser().parse_args(cmd.split())

    # Then
    assert namespace.mode == const.SUBCOMMAND__COLUMN_INDICES
    assert namespace.input_file == expected_input
    assert namespace.output_file == expected_output
    assert namespace.output_file_delimiter == expected_output_delimiter
    assert namespace.summary_file == expected_summary
    assert namespace.reheader_mapping == expected_reheader
    assert namespace.reheader_append == expected_reheader_append
    assert namespace.forced_input_file_delimiter == expected_force_delimiter
    assert namespace.forced_header_row_index == expected_force_header_row_index
    assert namespace.columns == expected_columns


@pytest.mark.parametrize(
    "cmd",
    [
        pytest.param(
            "column-names in.csv out.csv --force-comma --force-header-row-index 1 -c col1 col2 -C opt-col4 opt-col5 -c col3 --output-as-tsv -r col1=COL1 col3=COL3 --reheader-append -s summary.json ",
            id="1",
        ),
        pytest.param(
            "column-names in.csv out.csv --force-comma --force-header-row-index 1 -c col1 col2 -C opt-col4 opt-col5 -c col3 --output-as-tsv -r col1=COL1 col3=COL3 -s summary.json ",
            id="1.1",
        ),
        pytest.param(
            "column-names in.csv out.csv --force-tab --force-header-row-index 1 -c col1 col2 -C opt-col4 opt-col5 -c col3 --output-as-tsv -r col1=COL1 col3=COL3 -s summary.json",
            id="2",
        ),
        pytest.param(
            "column-names in.csv out.csv --force-header-row-index 1 -c col1 col2 -C opt-col4 opt-col5 -c col3 --output-as-tsv -r col1=COL1 col3=COL3 -s summary.json",
            id="3",
        ),
        pytest.param(
            "column-names in.csv out.csv -c col1 col2 -C opt-col4 opt-col5 -c col3 --output-as-tsv -r col1=COL1 col3=COL3 -s summary.json",
            id="4",
        ),
        pytest.param(
            "column-names in.csv out.csv -c col1 col2 -C opt-col4 opt-col5 -c col3 -r col1=COL1 col3=COL3 -s summary.json",
            id="5",
        ),
        pytest.param(
            "column-names in.csv out.csv -c col1 col2 -C opt-col4 opt-col5 -c col3 -s summary.json",
            id="6",
        ),
        pytest.param(
            "column-names in.csv out.csv -c col1 col2 -C opt-col4 opt-col5 -c col3.csv",
            id="7",
        ),
        pytest.param(
            "column-names in.csv out.csv -c col1 col2 -C opt-col4 opt-col5 -c col3",
            id="8",
        ),
    ],
)
def test_get_argpaser__namespace__vars(cmd):
    # Given
    namespace = _parser.get_argparser().parse_args(cmd.split())
    expected_keys = [
        const.ARG_SUBCOMMAND,
        const.ARG_INPUT,
        const.ARG_OUTPUT,
        const.ARG_OUTPUT_DELIMITER,
        const.ARG_SUMMARY,
        const.ARG_REHEADER,
        const.ARG_REHEADER_APPEND,
        const.ARG_FORCE_HEADER_ROW_INDEX,
        const.ARG_FORCE_INPUT_DELIMITER,
        const.ARG_COLUMNS,
    ]

    # When
    namespace_dict = vars(namespace)
    actual_keys = list(namespace_dict.keys())

    # Then
    assert set(actual_keys) == set(expected_keys)
    assert namespace.mode == namespace_dict[const.ARG_SUBCOMMAND]
    assert namespace.input_file == namespace_dict[const.ARG_INPUT]
    assert namespace.output_file == namespace_dict[const.ARG_OUTPUT]
    assert namespace.output_file_delimiter == namespace_dict[const.ARG_OUTPUT_DELIMITER]
    assert namespace.summary_file == namespace_dict[const.ARG_SUMMARY]
    assert namespace.reheader_mapping == namespace_dict[const.ARG_REHEADER]
    assert namespace.reheader_append == namespace_dict[const.ARG_REHEADER_APPEND]
    assert (
        namespace.forced_input_file_delimiter
        == namespace_dict[const.ARG_FORCE_INPUT_DELIMITER]
    )
    assert namespace.columns == namespace_dict[const.ARG_COLUMNS]


def test_get_argparser__sub_command__json():
    # Given
    cmd = "json in.json"
    expected_input = Path("in.json")

    # When
    namespace = _parser.get_argparser().parse_args(cmd.split())

    # Then
    assert namespace.mode == const.SUBCOMMAND__JSON
    assert namespace.input_file == expected_input


def test__prefix_column():
    # Given
    column = "col1"
    prefix = const.ARGPREFIX__REQUIRED_COLUMN
    expected = f"{prefix}{column}"

    # When
    actual = _parser._prefix_column(column, prefix)

    # Then
    assert actual == expected


def test__label_required_column():
    # Given
    column = "col1"
    expected = f"{const.ARGPREFIX__REQUIRED_COLUMN}{column}"

    # When
    actual = _parser._label_required_column(column)

    # Then
    assert actual == expected


def test__label_optional_column():
    # Given
    column = "col1"
    expected = f"{const.ARGPREFIX__OPTIONAL_COLUMN}{column}"

    # When
    actual = _parser._label_optional_column(column)

    # Then
    assert actual == expected


def test_parse_reheader_columns_valid():
    # Given
    columns = ["col1=COL1", "col2=COL2"]
    expected = {"col1": "COL1", "col2": "COL2"}

    # When
    actual = _parser.parse_reheader_columns(columns)

    # Then
    assert actual == expected


def test_parse_reheader_columns_valid_multiple_equals():
    # Given
    columns = ["col1=COL1=Extra", "col2=COL2"]
    expected = {"col1": "COL1=Extra", "col2": "COL2"}

    # When
    actual = _parser.parse_reheader_columns(columns)

    # Then
    assert actual == expected


# Test for invalid column mappings - no equal signs
def test_parse_reheader_columns_invalid_no_equals():
    # Given
    columns = ["col1COL1", "col2=COL2"]

    # When
    with pytest.raises(ValidationError):
        _parser.parse_reheader_columns(columns)


@pytest.mark.parametrize(
    "input_list,expected",
    [
        # Testing valid cases
        (["1", "2", "3"], [1, 2, 3]),
        (["0", "-2", "5"], [0, -2, 5]),
        ([], []),
    ],
)
def test_parse_integer_like_list_valid_cases(input_list, expected):
    # When
    actual = _parser.parse_integer_like_list(input_list)

    # Then
    assert actual == expected


@pytest.mark.parametrize(
    "input_list",
    [(["1", "2", "a"])],
)
def test_parse_integer_like_list_invalid_cases(input_list):
    # When
    with pytest.raises(ValidationError):
        _parser.parse_integer_like_list(input_list)


@pytest.mark.parametrize(
    "input_dict,expected",
    [
        # Testing valid cases
        ({"1": "col1", "2": "col2", "3": "col3"}, {1: "col1", 2: "col2", 3: "col3"}),
        ({"0": "col1", "-2": "col2", "5": "col3"}, {0: "col1", -2: "col2", 5: "col3"}),
        ({}, {}),
    ],
)
def test_parse_integer_like_dict_valid_cases(input_dict, expected):
    # When
    actual = _parser.parse_integer_like_dict(input_dict)

    # Then
    assert actual == expected


@pytest.mark.parametrize(
    "input_dict",
    [
        # Testing invalid cases
        ({"1": "col1", "2": "col2", "a": "col3"}),
        ({"1": "col1", "2": "col2", "": "col3"}),
    ],
)
def test_parse_integer_like_dict_invalid_cases(input_dict):
    # When
    with pytest.raises(ValidationError):
        _parser.parse_integer_like_dict(input_dict)
