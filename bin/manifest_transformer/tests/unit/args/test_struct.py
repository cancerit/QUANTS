import typing as t
from pathlib import Path

from src.args import _parser
from src.args import _struct
from src.enums import ColumnMode
from src.args._json_helper import load_json_file

from tests.test_data import files

# TESTS


def test_CleanArgs__with_column_names(make_csv_file):
    # Given
    input_file = make_csv_file()
    cmd = (
        f"column-names -i {str(input_file)} -o out.tsv "
        "--force-comma --force-header-row-index 1 "
        "-c col1 col2 -C opt-col4 opt-col5 -c col3 "
        "--output-as-tsv "
        "-s summary.json "
        "-r col1=COL1 col3=COL3 "
    )
    expected = _struct.CleanArgs(
        is_1_indexed=True,
        mode=ColumnMode.COLUMN_NAMES,
        input_file=input_file,
        output_file=Path("out.tsv"),
        summary_file=Path("summary.json"),
        column_order=("col1", "col2", "opt-col4", "opt-col5", "col3"),
        required_columns=("col1", "col2", "col3"),
        optional_columns=("opt-col4", "opt-col5"),
        output_file_delimiter="\t",
        forced_input_file_delimiter=",",
        forced_header_row_index=1,
        reheader_mapping={"col1": "COL1", "col3": "COL3"},
        reheader_append=False,
    )

    # When
    namespace = _parser.get_argparser().parse_args(cmd.split())
    actual = _struct.CleanArgs.from_namespace(namespace)

    # Then
    assert actual == expected


def test_CleanArgs__with_column_indices(make_csv_file):
    # Given
    input_file = make_csv_file()
    cmd = (
        f"column-indices -i {str(input_file)} -o out.csv "
        "--force-header-row-index 1 "
        "-c 1 2 -C 4 5 -c 3 "
        "-s summary.json "
        "-r 1=COL1 2=COL2 3=COL3 4=COL4 5=COL5 "
        "--reheader-append"
    )
    expected = _struct.CleanArgs(
        is_1_indexed=True,
        mode=ColumnMode.COLUMN_INDICES,
        input_file=input_file,
        output_file=Path("out.csv"),
        summary_file=Path("summary.json"),
        column_order=(1, 2, 4, 5, 3),
        required_columns=(1, 2, 3),
        optional_columns=(4, 5),
        output_file_delimiter=",",
        forced_input_file_delimiter=None,
        forced_header_row_index=1,
        reheader_mapping={1: "COL1", 2: "COL2", 3: "COL3", 4: "COL4", 5: "COL5"},
        reheader_append=True,
    )

    # When
    namespace = _parser.get_argparser().parse_args(cmd.split())
    actual = _struct.CleanArgs.from_namespace(namespace)

    # Then
    assert actual == expected


def test_CleanArgs__json__with_column_names():
    # Given
    json_param = files.example_json_params_1_column_names()
    expected = _struct.CleanArgs(
        is_1_indexed=True,
        mode=ColumnMode.COLUMN_NAMES,
        input_file=Path("tests/test_data/example_data_1_w_column_headers.csv"),
        output_file=Path("example_data_1_w_column_headers.output.csv"),
        summary_file=Path("example_data_1_w_column_headers.summary.json"),
        column_order=(
            "oligo_name",
            "species",
            "assembly",
            "gene_id",
            "transcript_id",
            "src_type",
            "ref_chr",
            "ref_strand",
            "ref_start",
            "ref_end",
        ),
        required_columns=(
            "oligo_name",
            "species",
            "assembly",
            "gene_id",
            "transcript_id",
        ),
        optional_columns=("src_type", "ref_chr", "ref_strand", "ref_start", "ref_end"),
        output_file_delimiter=",",
        forced_input_file_delimiter=None,
        forced_header_row_index=None,
        reheader_mapping={
            "oligo_name": "OLIGO_NAME",
            "species": "SPECIES",
            "assembly": "ASSEMBLY",
            "gene_id": "GENE_ID",
        },
        reheader_append=False,
    )

    # When
    as_dict = load_json_file(json_param)
    actual = _struct.CleanArgs.from_dict(as_dict)

    # Then
    assert actual == expected


def test_CleanArgs__json__with_column_indices():
    # Given
    json_param = files.example_json_params_1_column_indices()
    expected = _struct.CleanArgs(
        is_1_indexed=True,
        mode=ColumnMode.COLUMN_INDICES,
        input_file=Path("tests/test_data/example_data_1_w_column_headers.csv"),
        output_file=Path("example_data_1_w_column_headers.output.csv"),
        summary_file=Path("example_data_1_w_column_headers.summary.json"),
        column_order=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
        required_columns=(1, 2, 3, 4, 5),
        optional_columns=(6, 7, 8, 9, 10),
        output_file_delimiter=",",
        forced_input_file_delimiter=None,
        forced_header_row_index=None,
        reheader_mapping={
            1: "OLIGO_NAME",
            2: "SPECIES",
            3: "ASSEMBLY",
            4: "GENE_ID",
            5: "TRANSCRIPT_ID",
            6: "SRC_TYPE",
            7: "REF_CHR",
            8: "REF_STRAND",
            9: "REF_START",
            10: "REF_END",
        },
        reheader_append=True,
    )

    # When
    as_dict = load_json_file(json_param)
    actual = _struct.CleanArgs.from_dict(as_dict)

    # Then
    assert actual == expected


def test_CleanArgs__convert_to_0_indexed_and_back_to_1_indexed(make_csv_file):
    # Given
    input_file = make_csv_file()
    start_clean_args = _struct.CleanArgs(
        is_1_indexed=True,
        mode=ColumnMode.COLUMN_INDICES,
        input_file=input_file,
        output_file=Path("out.csv"),
        summary_file=Path("summary.json"),
        column_order=(1, 2, 4, 5, 3),
        required_columns=(1, 2, 3),
        optional_columns=(4, 5),
        output_file_delimiter=",",
        forced_input_file_delimiter=None,
        forced_header_row_index=1,
        reheader_mapping={
            1: "COL1",
            2: "COL2",
            3: "COL3",
            4: "COL4",
            5: "COL5",
        },
        reheader_append=True,
    )

    # When
    intermediate = start_clean_args.copy_as_0_indexed()

    # Next
    assert intermediate.is_1_indexed == False
    assert intermediate.column_order == (0, 1, 3, 4, 2)
    assert intermediate.required_columns == (0, 1, 2)
    assert intermediate.optional_columns == (3, 4)
    assert intermediate.forced_header_row_index == 0
    assert intermediate.reheader_mapping == {
        0: "COL1",
        1: "COL2",
        2: "COL3",
        3: "COL4",
        4: "COL5",
    }

    # Then
    end_clean_args = intermediate.copy_as_1_indexed()

    # Finally
    assert end_clean_args.is_1_indexed == True
    assert end_clean_args == start_clean_args
