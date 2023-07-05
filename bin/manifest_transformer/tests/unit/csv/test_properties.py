from pathlib import Path
import typing as t

import pytest

from src.csv import properties as csv_props
from tests.test_data import get

# CONSTANTS
CSV1_COLUMN_HEADERS = [
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
    "revc",
    "ref_seq",
    "pam_seq",
    "vcf_alias",
    "vcf_var_id",
    "mut_position",
    "ref",
    "new",
    "ref_aa",
    "alt_aa",
    "mut_type",
    "mutator",
    "oligo_length",
    "mseq",
]
CSV2_COLUMN_HEADERS = [
    "#id",
    "new",
    "ref_aa",
    "alt_aa",
]
CSV3_COLUMN_HEADERS = [
    "#oligo_name",
    "species",
    "assembly",
    "gene_id",
    "transcript_id",
    "src_type",
    "ref_chr",
    "ref_strand",
    "ref_start",
    "ref_end",
    "revc",
    "ref_seq",
    "pam_seq",
    "vcf_alias",
    "vcf_var_id",
    "mut_position",
    "ref",
    "new",
    "ref_aa",
    "alt_aa",
    "mut_type",
    "mutator",
    "oligo_length",
    "mseq",
]

MAPPING_HEADER_NAMES = {
    get.example_csv_1_with_column_headers(): ["oligo_name", "species", "assembly"],
    get.example_csv_1_without_headers(): ["new", "ref_aa", "alt_aa"],
    get.example_tsv_2_with_column_headers(): [
        "sgrna_ids",
        "sgrna_seqs",
        "gene_pair_id",
    ],
    get.example_tsv_2_with_file_and_column_headers(): [
        "#id",
        "sgrna_seqs",
        "gene_pair_id",
    ],
    get.example_tsv_2_without_headers(): ["sgrna_seqs", "gene_pair_id"],
    get.example_csv_3_with_file_and_column_headers(): [
        "#oligo_name",
        "species",
        "assembly",
    ],
    get.example_csv_3_with_column_headers(): [
        "ref_start",
        "ref_end",
        "revc",
    ],
    get.example_csv_3_without_headers(): [
        "mutator",
        "oligo_length",
        "mseq",
    ],
}
MAPPING_DELIMETER = {
    get.example_csv_1_with_column_headers(): ",",
    get.example_csv_1_without_headers(): ",",
    get.example_tsv_2_with_column_headers(): "\t",
    get.example_tsv_2_with_file_and_column_headers(): "\t",
    get.example_tsv_2_without_headers(): "\t",
    get.example_csv_3_with_file_and_column_headers(): ",",
    get.example_csv_3_with_column_headers(): ",",
    get.example_csv_3_without_headers(): ",",
}

# PARAMS

TEST_CASES = [
    (
        get.example_csv_1_with_column_headers(),
        csv_props.CSVFileProperties(
            dialect=None,
            file_offset=0,
            column_headers_line_index=0,
            file_headers_line_indices=[],
        ),
        "csv 1 with column headers",
    ),
    (
        get.example_csv_1_without_headers(),
        csv_props.CSVFileProperties(
            dialect=None,
            file_offset=0,
            column_headers_line_index=-1,
            file_headers_line_indices=[],
        ),
        "csv 1 without column headers",
    ),
    (
        get.example_tsv_2_with_file_and_column_headers(),
        csv_props.CSVFileProperties(
            dialect=None,
            file_offset=136,
            column_headers_line_index=2,
            file_headers_line_indices=[0, 1],
        ),
        "csv 2 with file and column headers",
    ),
    (
        get.example_tsv_2_with_column_headers(),
        csv_props.CSVFileProperties(
            dialect=None,
            file_offset=0,
            column_headers_line_index=0,
            file_headers_line_indices=[],
        ),
        "csv 2 with column headers",
    ),
    (
        get.example_tsv_2_without_headers(),
        csv_props.CSVFileProperties(
            dialect=None,
            file_offset=0,
            column_headers_line_index=-1,
            file_headers_line_indices=[],
        ),
        "csv 2 without column headers",
    ),
    (
        get.example_csv_3_with_file_and_column_headers(),
        csv_props.CSVFileProperties(
            dialect=None,
            file_offset=100,
            column_headers_line_index=2,
            file_headers_line_indices=[0, 1],
        ),
        "csv 3 with file and column headers",
    ),
    (
        get.example_csv_3_with_column_headers(),
        csv_props.CSVFileProperties(
            dialect=None,
            file_offset=0,
            column_headers_line_index=0,
            file_headers_line_indices=[],
        ),
        "csv 3 with column headers",
    ),
    (
        get.example_csv_3_without_headers(),
        csv_props.CSVFileProperties(
            dialect=None,
            file_offset=0,
            column_headers_line_index=-1,
            file_headers_line_indices=[],
        ),
        "csv 3 without column headers",
    ),
]
PROPERTIES_PARAMS = [
    pytest.param(file, props, id=id_) for file, props, id_ in TEST_CASES
]
PROPERTIES_AND_COLUMN_HEADER_PARAMS = [
    pytest.param(file, props, MAPPING_HEADER_NAMES[file], id=id_)
    for file, props, id_ in TEST_CASES
]
DELIMETER_PARAMS = [
    pytest.param(file, MAPPING_DELIMETER[file], id=id_) for file, _, id_ in TEST_CASES
]


@pytest.mark.parametrize("csv_file, expected_properties", PROPERTIES_PARAMS)
def test_CSVFileProperties__from_csv_file(
    csv_file: Path, expected_properties: csv_props.CSVFileProperties
):
    # Given
    expected_properties.dialect = csv_props.find_csv_dialect(csv_file)
    expected_dialect = expected_properties.dialect

    # When
    actual_properties = csv_props.CSVFileProperties.from_csv_file(csv_file)
    acutal_dialect = actual_properties.dialect

    # Then
    assert actual_properties == expected_properties
    eq_dialect = all(
        [
            acutal_dialect.delimiter == expected_dialect.delimiter,
            acutal_dialect.doublequote == expected_dialect.doublequote,
            acutal_dialect.escapechar == expected_dialect.escapechar,
            acutal_dialect.lineterminator == expected_dialect.lineterminator,
            acutal_dialect.quotechar == expected_dialect.quotechar,
            acutal_dialect.quoting == expected_dialect.quoting,
            acutal_dialect.skipinitialspace == expected_dialect.skipinitialspace,
        ]
    )
    assert eq_dialect


@pytest.mark.parametrize("csv_file, expected_properties", PROPERTIES_PARAMS)
def test_find_file_headers(
    csv_file: Path, expected_properties: csv_props.CSVFileProperties
):
    # Given
    expected_file_header_indices = expected_properties.file_headers_line_indices

    # When
    actual_header_indices = csv_props.find_file_headers(csv_file)

    # Then
    assert tuple(actual_header_indices) == expected_file_header_indices


@pytest.mark.parametrize(
    "csv_file, expected_properties, header_names", PROPERTIES_AND_COLUMN_HEADER_PARAMS
)
def test_find_column_headers_by_name(
    csv_file: Path,
    expected_properties: csv_props.CSVFileProperties,
    header_names: t.List[str],
):
    # Given
    expected_index = expected_properties.column_headers_line_index

    # When
    actual_index = csv_props.find_column_headers_by_name(csv_file, header_names)

    # Then
    assert actual_index == expected_index


@pytest.mark.parametrize("csv_file, expected_properties", PROPERTIES_PARAMS)
def test_find_column_headers_by_heuristic(
    csv_file: Path,
    expected_properties: csv_props.CSVFileProperties,
):
    # Given
    expected_index = expected_properties.column_headers_line_index

    # When
    actual_index = csv_props.find_column_headers_by_heuristic(csv_file)

    # Then
    assert actual_index == expected_index


@pytest.mark.parametrize("csv_file, expected_delimeter", DELIMETER_PARAMS)
def test_find_csv_dialect(csv_file: Path, expected_delimeter: str):
    # When
    actual_delimeter = csv_props.find_csv_dialect(csv_file)
    prompt = expected_delimeter
    actual_delimeter_with_prompt = csv_props.find_csv_dialect(
        csv_file, delimiters=prompt
    )

    # Then
    assert actual_delimeter.delimiter == expected_delimeter
    assert actual_delimeter_with_prompt.delimiter == expected_delimeter
