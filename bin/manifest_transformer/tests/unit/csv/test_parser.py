import typing as t
from pathlib import Path

import pytest

from src.csv.parser import CSVParser
from src.csv.properties import (
    CSVFileProperties,
    find_first_tabular_line_index_and_offset,
)
from src.exceptions import UserInterventionRequired
from tests.test_data import files, const

# PARAMS
CSV_FILE_READER_LINE_PARAMS = [
    # csv_file_path, first_line, second_line
    pytest.param(
        files.example_csv_1_without_headers,
        const.CSV1_DATA_ROW_1,
        const.CSV1_DATA_ROW_2,
        id="csv1+no_headers",
    ),
    pytest.param(
        files.example_csv_1_with_column_headers,
        const.CSV1_COLUMN_HEADERS,
        const.CSV1_DATA_ROW_1,
        id="csv1+col_headers",
    ),
    pytest.param(
        files.example_tsv_2_without_headers,
        const.TSV2_DATA_ROW_1,
        const.TSV2_DATA_ROW_2,
        id="tsv2+no_headers",
    ),
    pytest.param(
        files.example_tsv_2_with_column_headers,
        const.TSV2_COLUMN_HEADERS,
        const.TSV2_DATA_ROW_1,
        id="tsv2+col_headers",
    ),
    pytest.param(
        files.example_tsv_2_with_file_and_column_headers,
        const.TSV2_COLUMN_HEADERS,
        const.TSV2_DATA_ROW_1,
        id="tsv2+file+col_headers",
    ),
    pytest.param(
        files.example_csv_3_without_headers,
        const.CSV3_DATA_ROW_1,
        const.CSV3_DATA_ROW_2,
        id="csv3+no_headers",
    ),
    pytest.param(
        files.example_csv_3_with_column_headers,
        const.CSV3_COLUMN_HEADERS,
        const.CSV3_DATA_ROW_1,
        id="csv3+col_headers",
    ),
    pytest.param(
        files.example_csv_3_with_file_and_column_headers,
        const.CSV3_COLUMN_HEADERS,
        const.CSV3_DATA_ROW_1,
        id="csv3+file+col_headers",
    ),
]


CSV_FILE_COLUMN_PARAMS = [
    # With column headers
    # csv_file_path, expected_column_names, should_throw
    pytest.param(
        files.example_csv_1_with_column_headers,
        const.CSV1_COLUMN_HEADERS,
        False,
        id="csv1+col_headers",
    ),
    pytest.param(
        files.example_tsv_2_with_column_headers,
        const.TSV2_COLUMN_HEADERS,
        False,
        id="tsv2+col_headers",
    ),
    pytest.param(
        files.example_tsv_2_with_file_and_column_headers,
        const.TSV2_COLUMN_HEADERS,
        False,
        id="tsv2+file+col_headers",
    ),
    pytest.param(
        files.example_csv_3_with_column_headers,
        const.CSV3_COLUMN_HEADERS,
        False,
        id="csv3+col_headers",
    ),
    pytest.param(
        files.example_csv_3_with_file_and_column_headers,
        const.CSV3_COLUMN_HEADERS,
        False,
        id="csv3+file+col_headers",
    ),
    # Without column headers
    # csv_file_path, expected_column_names, should_throw
    pytest.param(
        files.example_csv_1_without_headers,
        [],
        True,
        id="csv1+no_headers#error",
    ),
    pytest.param(
        files.example_tsv_2_without_headers,
        [],
        True,
        id="tsv2+no_headers#error",
    ),
    pytest.param(
        files.example_csv_3_without_headers,
        [],
        True,
        id="csv3+no_headers#error",
    ),
]


CSV_FILE_INDICES_PARAMS = [
    # csv_file_path, expected_column_indices
    pytest.param(
        files.example_csv_1_with_column_headers,
        list(range(len(const.CSV1_COLUMN_HEADERS))),
        id="csv1+col_headers",
    ),
    pytest.param(
        files.example_csv_1_without_headers,
        list(range(len(const.CSV1_COLUMN_HEADERS))),
        id="csv1",
    ),
    pytest.param(
        files.example_tsv_2_with_column_headers,
        list(range(len(const.TSV2_COLUMN_HEADERS))),
        id="tsv2+col_headers",
    ),
    pytest.param(
        files.example_tsv_2_with_file_and_column_headers,
        list(range(len(const.TSV2_COLUMN_HEADERS))),
        id="tsv2+file+col_headers",
    ),
    pytest.param(
        files.example_tsv_2_without_headers,
        list(range(len(const.TSV2_COLUMN_HEADERS))),
        id="tsv2",
    ),
    pytest.param(
        files.example_csv_3_with_column_headers,
        list(range(len(const.CSV3_COLUMN_HEADERS))),
        id="csv3+col_headers",
    ),
    pytest.param(
        files.example_csv_3_with_file_and_column_headers,
        list(range(len(const.CSV3_COLUMN_HEADERS))),
        id="csv3+file+col_headers",
    ),
    pytest.param(
        files.example_csv_3_without_headers,
        list(range(len(const.CSV3_COLUMN_HEADERS))),
        id="csv3",
    ),
]

COLUMN_COUNT_PARAMS = [
    # With normal CSV file
    # columns, include_file_header, include_column_header, use_erroneous_csv_file, expected
    pytest.param(5, True, True, False, (5, True), id="5cols+file_header+col_header"),
    pytest.param(5, True, False, False, (5, True), id="5cols+file_header"),
    pytest.param(5, False, True, False, (5, True), id="5cols+col_header"),
    pytest.param(5, False, False, False, (5, True), id="5cols"),
    # With erroneous CSV file
    # columns, include_file_header, include_column_header, use_erroneous_csv_file, expected
    pytest.param(
        5, True, True, True, (5, False), id="5cols+file_header+col_header#invalid"
    ),
    pytest.param(5, True, False, True, (5, False), id="5cols+file_header#invalid"),
    pytest.param(5, False, True, True, (5, False), id="5cols+col_header#invalid"),
    pytest.param(5, False, False, True, (5, False), id="5cols#invalid"),
]


# TESTS
@pytest.mark.parametrize(
    "get_csv_path, expected_first_row, expected_second_row", CSV_FILE_READER_LINE_PARAMS
)
def test_CSVParser_get_csv_reader(
    get_csv_path: t.Callable[[], Path],
    expected_first_row: t.List[str],
    expected_second_row: t.List[str],
):
    # Given
    csv_file_path = get_csv_path()
    csv_properties = CSVFileProperties.from_csv_file(csv_file_path)
    parser = CSVParser.from_csv_file_properties(csv_file_path, csv_properties)

    # When
    with parser.get_csv_reader() as csv_reader:
        actual_first_row = next(csv_reader)
        actual_second_row = next(csv_reader)

    # Then
    assert actual_first_row == expected_first_row
    assert actual_second_row == expected_second_row


@pytest.mark.parametrize(
    "get_csv_path, expected_column_names, should_throw", CSV_FILE_COLUMN_PARAMS
)
def test_CSVParser_column_header_names(
    get_csv_path: t.Callable[[], Path],
    expected_column_names: t.List[str],
    should_throw: bool,
):
    # Given
    csv_file_path = get_csv_path()
    csv_properties = CSVFileProperties.from_csv_file(csv_file_path)
    parser = CSVParser.from_csv_file_properties(csv_file_path, csv_properties)
    expected = tuple(expected_column_names)

    if should_throw:
        # When and Then
        with pytest.raises(RuntimeError):
            parser.column_header_names()
    else:
        # When
        actual_column_names = parser.column_header_names()

        # Then
        assert actual_column_names == expected


@pytest.mark.parametrize(
    "get_csv_path, expected_column_indices", CSV_FILE_INDICES_PARAMS
)
def test_CSVParser_column_indices(
    get_csv_path: t.Callable[[], Path],
    expected_column_indices: t.List[int],
):
    # Given
    csv_file_path = get_csv_path()
    csv_properties = CSVFileProperties.from_csv_file(csv_file_path)
    parser = CSVParser.from_csv_file_properties(csv_file_path, csv_properties)
    expected = tuple(expected_column_indices)

    # When
    actual_column_names = parser.column_indices()

    # Then
    assert actual_column_names == expected


def test_CSVParser_count_columns_comprehensively__simple(
    make_csv_file: t.Callable[[bool, int, bool, bool], Path],
):
    # Given
    columns = 5
    csv_file_path = make_csv_file(
        is_erroneous=True,
        columns=columns,
        include_file_header=True,
        include_column_header=True,
    )
    _, offset = find_first_tabular_line_index_and_offset(csv_file_path)

    # When
    parser = CSVParser(
        csv_file_path,
        has_header=True,
        offset=offset,
        dialect=None,
        delimiter=",",  # Force delimiter, ignore dialect
    )
    actual_simple_count = parser.count_columns()
    actual_comp_count = parser.count_columns_comprehensively()

    # Then
    assert actual_simple_count == 5
    assert actual_comp_count == (5, False)


@pytest.mark.parametrize(
    "columns, include_file_header, include_column_header, use_erroneous_csv_file, expected",
    COLUMN_COUNT_PARAMS,
)
def test_CSVParser_count_columns_comprehensively__via_CSVFileProperties(
    columns: int,
    include_file_header: bool,
    include_column_header: bool,
    use_erroneous_csv_file: bool,
    expected: t.Tuple[int, bool],
    make_csv_file: t.Callable[[bool, int, bool, bool], Path],
):
    # Given
    assert columns == expected[0], "Precondition: columns must match expected"
    csv_file_path = make_csv_file(
        is_erroneous=use_erroneous_csv_file,
        columns=columns,
        include_file_header=include_file_header,
        include_column_header=include_column_header,
    )

    # Given - extended setup
    # If the CSV file is erroneous, the user will be
    # prompted to take action to fix it. This is simulated by the following try/except
    try:
        csv_properties = CSVFileProperties.from_csv_file(csv_file_path)
    except UserInterventionRequired:
        # Rescue functionality via user intervention by setting a forced
        # delimiter and using column names to find the column header index
        csv_properties = CSVFileProperties.from_csv_file(
            csv_file_path,
            column_names="col_0,col_1,col_2,col_3,col_4".split(","),
            forced_delimiter=",",
        )

    # When
    parser = CSVParser.from_csv_file_properties(csv_file_path, csv_properties)
    actual_simple_count = parser.count_columns()
    actual_comp_count = parser.count_columns_comprehensively()

    # Then
    assert actual_simple_count == expected[0]
    assert actual_comp_count == expected


@pytest.mark.parametrize("has_null_values", [True, False])
@pytest.mark.parametrize(
    "null_value",
    ["NA", "NULL", "", "N/A", "NAN", "NaN", "na", "Na", "n/a", "Nan", "nan"],
)
def test_CSVParser_find_rows_with_nulls(make_csv_file, has_null_values, null_value):
    # Given
    csv_file_path = make_csv_file(
        is_erroneous=False,
        columns=5,
        include_file_header=True,
        include_column_header=True,
        include_null_values=has_null_values,
        null_value=null_value,
    )
    csv_properties = CSVFileProperties.from_csv_file(csv_file_path)
    expected = set(range(1, 11)) if has_null_values else set([0])

    # When
    parser = CSVParser.from_csv_file_properties(csv_file_path, csv_properties)
    null_rows = parser.find_rows_with_nulls()

    # Then
    assert len(null_rows) in expected, csv_file_path.read_text()


@pytest.mark.parametrize("has_null_values", [True, False])
@pytest.mark.parametrize("null_value", ["none", "nil", " "])
def test_CSVParser_find_rows_with_nulls__using_non_default_null_values(
    make_csv_file, has_null_values, null_value
):
    # Given
    csv_file_path = make_csv_file(
        is_erroneous=False,
        columns=5,
        include_file_header=True,
        include_column_header=True,
        include_null_values=has_null_values,
        null_value=null_value,
    )
    csv_properties = CSVFileProperties.from_csv_file(csv_file_path)
    expected = set(range(1, 11)) if has_null_values else set([0])

    # When
    parser = CSVParser.from_csv_file_properties(csv_file_path, csv_properties)
    null_rows = parser.find_rows_with_nulls(extra_null_values=[null_value])

    # Then
    assert len(null_rows) in expected, csv_file_path.read_text()
