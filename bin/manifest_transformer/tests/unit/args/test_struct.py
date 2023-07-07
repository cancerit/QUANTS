from pathlib import Path

from src.args import parser
from src.args import struct
from src.enums import ColumnMode

# TESTS


def test_CleanArgs__with_column_names(make_csv_file):
    # Given
    input_file = make_csv_file()
    cmd = (
        f"column-names {str(input_file)} "
        "--force-comma --force-header-row-index 1 "
        "-c col1 col2 -C opt-col4 opt-col5 -c col3 "
        "-o out.tsv --output-as-tsv "
        "-s summary.json "
        "-r col1=COL1 col3=COL3"
    )
    expected = struct.CleanArgs(
        is_1_indexed=True,
        mode=ColumnMode.COLUMN_NAMES,
        input_file=input_file,
        output_file=Path("out.tsv"),
        summary_file=Path("summary.json"),
        column_order=("col1", "col2", "opt-col4", "opt-col5", "col3"),
        required_columns=("col1", "col2", "col3"),
        optional_columns=("opt-col4", "opt-col5"),
        output_file_delimiter="\t",
        forced_intput_file_delimiter=",",
        forced_header_row_index=1,
        reheader_mapping={"col1": "COL1", "col3": "COL3"},
    )

    # When
    namespace = parser.get_argparser().parse_args(cmd.split())
    actual = struct.CleanArgs.from_namespace(namespace)

    # Then
    assert actual == expected


def test_CleanArgs__with_column_indices(make_csv_file):
    # Given
    input_file = make_csv_file()
    cmd = (
        f"column-indices {str(input_file)} "
        "--force-header-row-index 1 "
        "-c 1 2 -C 4 5 -c 3 "
        "-o out.csv "
        "-s summary.json "
        "-r 1=COL1 3=COL3"
    )
    expected = struct.CleanArgs(
        is_1_indexed=True,
        mode=ColumnMode.COLUMN_INDICES,
        input_file=input_file,
        output_file=Path("out.csv"),
        summary_file=Path("summary.json"),
        column_order=(1, 2, 4, 5, 3),
        required_columns=(1, 2, 3),
        optional_columns=(4, 5),
        output_file_delimiter=",",
        forced_intput_file_delimiter=None,
        forced_header_row_index=1,
        reheader_mapping={1: "COL1", 3: "COL3"},
    )

    # When
    namespace = parser.get_argparser().parse_args(cmd.split())
    actual = struct.CleanArgs.from_namespace(namespace)

    # Then
    assert actual == expected


def test_CleanArgs__convert_to_0_indexed_and_back_to_1_indexed(make_csv_file):
    # Given
    input_file = make_csv_file()
    start_clean_args = struct.CleanArgs(
        is_1_indexed=True,
        mode=ColumnMode.COLUMN_INDICES,
        input_file=input_file,
        output_file=Path("out.csv"),
        summary_file=Path("summary.json"),
        column_order=(1, 2, 4, 5, 3),
        required_columns=(1, 2, 3),
        optional_columns=(4, 5),
        output_file_delimiter=",",
        forced_intput_file_delimiter=None,
        forced_header_row_index=1,
        reheader_mapping={1: "COL1", 3: "COL3"},
    )

    # When
    intermediate = start_clean_args.copy_as_0_indexed()

    # Next
    assert intermediate.is_1_indexed == False
    assert intermediate.column_order == (0, 1, 3, 4, 2)
    assert intermediate.required_columns == (0, 1, 2)
    assert intermediate.optional_columns == (3, 4)
    assert intermediate.forced_header_row_index == 0
    assert intermediate.reheader_mapping == {0: "COL1", 2: "COL3"}

    # Then
    end_clean_args = intermediate.copy_as_1_indexed()

    # Finally
    assert end_clean_args.is_1_indexed == True
    assert end_clean_args == start_clean_args
