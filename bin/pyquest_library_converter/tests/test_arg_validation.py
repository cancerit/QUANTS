import typing as t
from dataclasses import dataclass
import argparse
from pathlib import Path

import pytest

from src.args.args_cleaner import ArgsCleaner
from src.args.args_parsing import get_argparser
from src.exceptions import ValidationError
from src import constants as const
from enum import IntEnum


class NameArg(IntEnum):
    HEADER = 1
    INDEX = 2


class SeqArg(IntEnum):
    HEADER = 1
    INDEX = 2


from tests import test_data

# FIXTURE HELPER


@dataclass
class ConfigData:
    csv_path: Path
    csv_delimiter: str
    file_header_rows: t.List[int]
    has_column_header_row: bool
    oligo_seq_name_header: str
    oligo_seq_name_index: int
    oligo_seq_header: str
    oligo_seq_index: int
    valid_namespace: argparse.Namespace
    valid_namespace_with_headers: argparse.Namespace


# FIXTURES
CSV_SYMBOL_1 = "example_data_1_csv"
CSV_SYMBOL_2 = "example_data_2_tsv"
CONFIG_PARAMS = [CSV_SYMBOL_1, CSV_SYMBOL_2]
EXAMPLE_OUTPUT_PATH = Path("example_output_path.csv")


@pytest.fixture(params=CONFIG_PARAMS)
def config(request):
    if request.param == CSV_SYMBOL_1:
        # Setup from _ExampleData1_Mixin
        csv_path = test_data.get.example_data_1_csv()  # replace with actual path
        csv_delimiter = ","
        file_header_rows = []
        has_column_header_row = True
        oligo_seq_name_header = "oligo_name"
        oligo_seq_name_index = 1  # 1-based indexing
        oligo_seq_header = "mseq"
        oligo_seq_index = 24  # 1-based indexing
        valid_namespace = argparse.Namespace(
            input_file=csv_path,
            output_file=EXAMPLE_OUTPUT_PATH,
            forward_primer="",
            reverse_primer="",
            reverse_complement_flag=False,
            skip_n_rows=0,
            name_header=None,
            name_index=oligo_seq_name_index,
            sequence_index=oligo_seq_index,
            sequence_header=None,
            verbose=False,
        )
        valid_namespace_with_headers = argparse.Namespace(
            input_file=csv_path,
            output_file=EXAMPLE_OUTPUT_PATH,
            forward_primer="",
            reverse_primer="",
            reverse_complement_flag=False,
            skip_n_rows=0,
            name_header=oligo_seq_name_header,
            name_index=None,
            sequence_header=oligo_seq_header,
            sequence_index=None,
            verbose=False,
        )
    elif request.param == CSV_SYMBOL_2:
        # Setup from _ExampleData2_Mixin
        csv_path = test_data.get.example_data_2_tsv()
        csv_delimiter = "\t"
        file_header_rows = [0, 1]
        has_column_header_row = True
        oligo_seq_name_header = "#id"
        oligo_seq_name_index = 1  # 1-based indexing
        oligo_seq_header = "sgrna_seqs"
        oligo_seq_index = 3  # 1-based indexing
        valid_namespace = argparse.Namespace(
            input_file=csv_path,
            output_file=EXAMPLE_OUTPUT_PATH,
            forward_primer="",
            reverse_primer="",
            reverse_complement_flag=False,
            skip_n_rows=0,
            name_header=None,
            name_index=oligo_seq_name_index,
            sequence_index=oligo_seq_index,
            sequence_header=None,
            verbose=False,
        )
        valid_namespace_with_headers = argparse.Namespace(
            input_file=csv_path,
            output_file=EXAMPLE_OUTPUT_PATH,
            forward_primer="",
            reverse_primer="",
            reverse_complement_flag=False,
            skip_n_rows=0,
            name_header=oligo_seq_name_header,
            name_index=None,
            sequence_header=oligo_seq_header,
            sequence_index=None,
            verbose=False,
        )
    else:
        raise ValueError(f"Invalid request.param: {request.param}")

    config = ConfigData(
        csv_path=csv_path,
        csv_delimiter=csv_delimiter,
        file_header_rows=file_header_rows,
        has_column_header_row=has_column_header_row,
        oligo_seq_name_header=oligo_seq_name_header,
        oligo_seq_name_index=oligo_seq_name_index,
        oligo_seq_header=oligo_seq_header,
        oligo_seq_index=oligo_seq_index,
        valid_namespace=valid_namespace,
        valid_namespace_with_headers=valid_namespace_with_headers,
    )
    return config


# TESTS


def test_validate__with_valid_namespace(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()


def test_validate__with_valid_namespace_with_headers(config):
    namespace = config.valid_namespace_with_headers
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()


@pytest.mark.parametrize(
    "cmd_fragment_template, name_type, seq_type, should_throw",
    [
        pytest.param("-N {} -S {}", NameArg.INDEX, SeqArg.INDEX, False, id="N+S"),
        pytest.param("-n {} -s {}", NameArg.HEADER, SeqArg.HEADER, False, id="n+s"),
        pytest.param("-N {} -s {}", NameArg.INDEX, SeqArg.HEADER, True, id="N+s"),
        pytest.param("-n {} -S {}", NameArg.INDEX, SeqArg.INDEX, True, id="n+S"),
    ],
)
def test_validate__throws_when_headers_and_names_are_mixed(
    config,
    cmd_fragment_template,
    name_type: NameArg,
    seq_type: SeqArg,
    should_throw: bool,
):
    # Given
    name_value = (
        config.oligo_seq_name_index
        if name_type == NameArg.INDEX
        else config.oligo_seq_name_header
    )
    seq_value = (
        config.oligo_seq_index if seq_type == SeqArg.INDEX else config.oligo_seq_header
    )
    cmd_fragment = cmd_fragment_template.format(name_value, seq_value)
    cmd = f"{str(config.valid_namespace.input_file)} {str(config.valid_namespace.output_file)} {cmd_fragment}"

    argparser = get_argparser()
    namespace = argparser.parse_args(cmd.split())
    # When
    args_cleaner = ArgsCleaner(namespace)
    if should_throw:
        # Then
        with pytest.raises(ValidationError):
            args_cleaner.validate()
        return
    else:
        # Then
        args_cleaner.validate()
        assert args_cleaner.get_clean_name_index() == config.oligo_seq_name_index
        assert args_cleaner.get_clean_sequence_index() == config.oligo_seq_index


def test_validate_codependent_input_args(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner._validate_codependent_input_args()


def test_validate_output(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner._validate_output()


def test_validate_output__throws_when_input_equals_output(config):
    namespace = config.valid_namespace
    namespace.input_file = config.csv_path
    namespace.output_file = config.csv_path
    args_cleaner = ArgsCleaner(namespace)
    with pytest.raises(ValidationError):
        args_cleaner.validate()


def test_validate_forward_primer(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner._validate_forward_primer()


PRIMER_TEST_CASES = [
    # sequence, should_throw
    # simple positive cases
    ("", False),
    ("A", False),
    ("C", False),
    ("G", False),
    ("T", False),
    # simple negative cases
    ("N", True),
    ("a", True),
    ("c", True),
    ("g", True),
    ("t", True),
    ("n", True),
] + [
    # complex postive cases
    ("ATCG", False),
    ("ATCGATCG", False),
    ("ATCGATCGATCGATCG", False),
    ("CATGAGGGAAGTCATCTGACAGAACAGCAGCACTTTGTGGTTGGTTGCTCGGAGTTTGG", False),
    # complex negative cases: illegal characters
    ("ATCGN", True),
    ("atcg", True),
    ("ATCGatcg", True),
    ("ATCGATCGatcg", True),
    ("AZCG", True),
    ("ATCGAACB", True),
    ("CATGAGGGAAGTCATCTGACAGA3CAGCAGCACTTTGTGGTTGGTTGCTCGGAGTTTGG", True),
    ("CATGAGGGAAGTCATCTGACAGA?CAGCAGCACTTTGTGGTTGGTTGCTCGGAGTTTGG", True),
    ("CATGAGGGAAGTCATCTGACAGAzCAGCAGCACTTTGTGGTTGGTTGCTCGGAGTTTGG", True),
]


@pytest.mark.parametrize("sequence, should_throw", PRIMER_TEST_CASES)
def test_validate_forward_primer__raises_if_illegal(config, sequence, should_throw):
    namespace = config.valid_namespace
    namespace.forward_primer = sequence
    args_cleaner = ArgsCleaner(namespace)
    if should_throw:
        with pytest.raises(ValidationError):
            args_cleaner.validate()
    else:
        args_cleaner.validate()
        actual = args_cleaner.get_clean_forward_primer()
        assert actual == sequence


@pytest.mark.parametrize("sequence, should_throw", PRIMER_TEST_CASES)
def test_validate_reverse_primer__raises_if_illegal(config, sequence, should_throw):
    namespace = config.valid_namespace
    namespace.reverse_primer = sequence
    args_cleaner = ArgsCleaner(namespace)
    if should_throw:
        with pytest.raises(ValidationError):
            args_cleaner.validate()
    else:
        args_cleaner.validate()

        actual = args_cleaner.get_clean_reverse_primer()
        assert actual == sequence


def test_validate_reverse_primer(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner._validate_reverse_primer()


def test_validate_reverse_complement_flag(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner._validate_reverse_complement_flag()


def test_validate_name_index(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    with pytest.raises(RuntimeError):
        args_cleaner._validate_name_index()
    args_cleaner._validate_codependent_input_args()
    args_cleaner._validate_name_index()


def test_validate_name_index_with_header(config):
    namespace = config.valid_namespace_with_headers
    args_cleaner = ArgsCleaner(namespace)
    with pytest.raises(RuntimeError):
        args_cleaner._validate_name_index()
    args_cleaner._validate_codependent_input_args()
    args_cleaner._validate_name_index()


def test_validate_sequence_index(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    with pytest.raises(RuntimeError):
        args_cleaner._validate_sequence_index()
    args_cleaner._validate_codependent_input_args()
    args_cleaner._validate_sequence_index()


def test_validate_sequence_index_with_header(config):
    namespace = config.valid_namespace_with_headers
    args_cleaner = ArgsCleaner(namespace)
    with pytest.raises(RuntimeError):
        args_cleaner._validate_sequence_index()
    args_cleaner._validate_codependent_input_args()
    args_cleaner._validate_sequence_index()


@pytest.mark.parametrize(
    "sequence_index,name_index,should_throw",
    [
        (1, 1, True),
        (1, 2, False),
        (2, 1, False),
        (2, 2, True),
    ],
)
def test_validate_sequence_index_and_name_index_are_not_the_same(
    config, sequence_index, name_index, should_throw
):
    namespace = config.valid_namespace
    namespace.sequence_index = sequence_index
    namespace.name_index = name_index
    args_cleaner = ArgsCleaner(namespace)
    if should_throw:
        with pytest.raises(ValidationError):
            args_cleaner.validate()
    else:
        args_cleaner.validate()


@pytest.mark.parametrize(
    "col1, col2, should_throw",
    [
        ("name", "sequence", False),
        ("sequence", "name", False),
        ("name", "name", True),
        ("sequence", "sequence", True),
    ],
)
@pytest.mark.parametrize("as_index", [True, False])
def test_validate_sequence_header_and_name_header_are_not_the_same(
    config, col1, col2, as_index, should_throw
):
    # Given
    namespace = config.valid_namespace_with_headers
    pick_index = (
        lambda x: config.oligo_seq_name_index
        if x == "sequence"
        else config.oligo_seq_index
    )
    pick_header = (
        lambda x: config.oligo_seq_name_header
        if x == "sequence"
        else config.oligo_seq_header
    )

    if as_index:
        col1_value = pick_index(col1)
        col2_value = pick_index(col2)
        namespace.sequence_index = col1_value
        namespace.sequence_header = None
        namespace.name_index = col2_value
        namespace.name_header = None
    else:
        col1_value = pick_header(col1)
        col2_value = pick_header(col2)
        namespace.sequence_index = None
        namespace.sequence_header = col1_value
        namespace.name_index = None
        namespace.name_header = col2_value
    args_cleaner = ArgsCleaner(namespace)

    # When / Then
    if should_throw:
        with pytest.raises(ValidationError):
            args_cleaner.validate()
    else:
        args_cleaner.validate()


def test_get_clean_input(config):
    namespace = config.valid_namespace
    expected_input = config.csv_path
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_input = args_cleaner.get_clean_input()
    assert expected_input == actual_input


def test_get_clean_adjusted_skip_n_rows(config):
    expected_skip_n_rows = (
        config.valid_namespace.skip_n_rows
        + config.has_column_header_row
        + len(config.file_header_rows)
    )
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_skip_n_rows = args_cleaner.get_clean_adjusted_skip_n_rows()
    assert expected_skip_n_rows == actual_skip_n_rows


def test_get_clean_adjusted_skip_n_rows__with_headers(config):
    expected_skip_n_rows = (
        config.valid_namespace.skip_n_rows
        + config.has_column_header_row
        + len(config.file_header_rows)
    )
    namespace = config.valid_namespace_with_headers
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_skip_n_rows = args_cleaner.get_clean_adjusted_skip_n_rows()
    assert expected_skip_n_rows == actual_skip_n_rows


def test_get_clean_output__with_specific_output_that_does_exist(config, tmp_path):
    expected_output = tmp_path / "foo.csv"
    expected_output.touch()
    namespace = config.valid_namespace
    namespace.output_file = expected_output
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_output = args_cleaner.get_clean_output()
    assert expected_output == actual_output


def test_get_clean_output__with_specific_output_that_doesnt_exist(config, tmp_path):
    expected_output = tmp_path / "foo.csv"
    namespace = config.valid_namespace
    namespace.output_file = expected_output
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_output = args_cleaner.get_clean_output()
    assert expected_output == actual_output


def test_get_clean_output__with_specific_output_dir(config):
    expected_output = (
        config.csv_path.parent / f"{config.csv_path.stem}.out{config.csv_path.suffix}"
    )
    namespace = config.valid_namespace
    namespace.output_file = config.csv_path.parent
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_output = args_cleaner.get_clean_output()
    assert expected_output == actual_output


def test_get_clean_forward_primer(config):
    expected_forward_primer = ""
    namespace = config.valid_namespace
    namespace.forward_primer = expected_forward_primer
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_forward_primer = args_cleaner.get_clean_forward_primer()
    assert expected_forward_primer == actual_forward_primer


def test_get_clean_forward_primer__with_chars(config):
    expected_forward_primer = "AATTAACG"
    namespace = config.valid_namespace
    namespace.forward_primer = expected_forward_primer
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_forward_primer = args_cleaner.get_clean_forward_primer()
    assert expected_forward_primer == actual_forward_primer


def test_get_clean_reverse_primer(config):
    expected_reverse_primer = ""
    namespace = config.valid_namespace
    namespace.reverse_primer = expected_reverse_primer
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_reverse_primer = args_cleaner.get_clean_reverse_primer()
    assert expected_reverse_primer == actual_reverse_primer


def test_get_clean_reverse_primer__with_chars(config):
    expected_reverse_primer = "AATTAACG"
    namespace = config.valid_namespace
    namespace.reverse_primer = expected_reverse_primer
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_reverse_primer = args_cleaner.get_clean_reverse_primer()
    assert expected_reverse_primer == actual_reverse_primer


def test_get_reverse_complement_flag(config):
    expected_reverse_complement_flag = True
    namespace = config.valid_namespace
    namespace.reverse_complement_flag = expected_reverse_complement_flag
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_reverse_complement_flag = args_cleaner.get_clean_reverse_complement_flag()
    assert expected_reverse_complement_flag == actual_reverse_complement_flag


def test_get_clean_verbose(config):
    expected_verbose = True
    namespace = config.valid_namespace
    namespace.verbose = expected_verbose
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_verbose = args_cleaner.get_clean_verbose()
    assert expected_verbose == actual_verbose


def test_get_clean_name_index(config):
    expected_name_index = config.oligo_seq_name_index
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_name_index = args_cleaner.get_clean_name_index()
    assert expected_name_index == actual_name_index


def test_get_clean_name_index_with_header(config):
    expected_name_index = config.oligo_seq_name_index
    namespace = config.valid_namespace_with_headers
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_name_index = args_cleaner.get_clean_name_index()
    assert expected_name_index == actual_name_index


def test_get_clean_sequence_index(config):
    expected_sequence_index = config.oligo_seq_index
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_sequence_index = args_cleaner.get_clean_sequence_index()
    assert expected_sequence_index == actual_sequence_index


def test_get_clean_sequence_index_with_header(config):
    expected_sequence_index = config.oligo_seq_index
    namespace = config.valid_namespace_with_headers
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_sequence_index = args_cleaner.get_clean_sequence_index()
    assert expected_sequence_index == actual_sequence_index


def test_to_clean_dict(config):
    # Given
    namespace = config.valid_namespace
    expected_dict = vars(namespace).copy()
    args_cleaner = ArgsCleaner(namespace)
    adjusted_skip_rows = (
        getattr(namespace, const._ARG_SKIP_N_ROWS)
        + config.has_column_header_row
        + len(config.file_header_rows)
    )
    ## ! Remove header key-values, as they will never be in clean dict
    ## Also relabel skip rows to adjusted skip rows
    expected_dict.pop(const._ARG_NAME_HEADER)
    expected_dict.pop(const._ARG_SEQ_HEADER)
    expected_dict.pop(const._ARG_SKIP_N_ROWS)
    expected_dict[const.KEY_ADJUSTED_SKIP_N_ROWS] = adjusted_skip_rows

    # When
    args_cleaner.validate()
    actual_dict = args_cleaner.to_clean_dict()

    # Then
    assert expected_dict == actual_dict


def test_to_clean_dict__with_header(config):
    import pandas as pd

    # Setup
    namespace = config.valid_namespace_with_headers
    df = pd.read_csv(
        namespace.input_file,
        sep=config.csv_delimiter,
        # We pandas to skip file header/file comments
        skiprows=len(config.file_header_rows),
    )
    name_index_1 = df.columns.get_loc(namespace.name_header) + 1
    sequence_index_1 = df.columns.get_loc(namespace.sequence_header) + 1
    adjusted_skip_rows = (
        getattr(namespace, const._ARG_SKIP_N_ROWS)
        + config.has_column_header_row
        + len(config.file_header_rows)
    )

    # Given
    args_cleaner = ArgsCleaner(namespace)
    ## ! Remove header key-values, as they will never be in clean dict
    ## ! Replace header key-values with index key-values, as they would be in clean dict
    ## Also relabel skip rows to adjusted skip rows
    expected_dict = vars(namespace).copy()
    expected_dict.pop(const._ARG_NAME_HEADER)
    expected_dict.pop(const._ARG_SEQ_HEADER)
    expected_dict[const._ARG_NAME_INDEX] = name_index_1
    expected_dict[const._ARG_SEQ_INDEX] = sequence_index_1
    expected_dict.pop(const._ARG_SKIP_N_ROWS)
    expected_dict[const.KEY_ADJUSTED_SKIP_N_ROWS] = adjusted_skip_rows

    # When
    args_cleaner.validate()
    actual_dict = args_cleaner.to_clean_dict()

    # Then
    assert expected_dict == actual_dict
