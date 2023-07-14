from dataclasses import dataclass
import argparse
import pytest
from pyquest_library_converter import ArgsCleaner, ValidationError
from tests import test_data
from pathlib import Path

# FIXTURE HELPER


@dataclass
class ConfigData:
    csv_path: Path
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
        oligo_seq_name_header = "oligo_name"
        oligo_seq_name_index = 1  # 1-based indexing
        oligo_seq_header = "mseq"
        oligo_seq_index = 24  # 1-based indexing
        valid_namespace = argparse.Namespace(
            input=csv_path,
            output=EXAMPLE_OUTPUT_PATH,
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
            input=csv_path,
            output=EXAMPLE_OUTPUT_PATH,
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
        return ConfigData(
            csv_path=csv_path,
            oligo_seq_name_header=oligo_seq_name_header,
            oligo_seq_name_index=oligo_seq_name_index,
            oligo_seq_header=oligo_seq_header,
            oligo_seq_index=oligo_seq_index,
            valid_namespace=valid_namespace,
            valid_namespace_with_headers=valid_namespace_with_headers,
        )
    elif request.param == CSV_SYMBOL_2:
        # Setup from _ExampleData2_Mixin
        csv_path = test_data.get.example_data_2_tsv()
        oligo_seq_name_header = "#id"
        oligo_seq_name_index = 1  # 1-based indexing
        oligo_seq_header = "sgrna_seqs"
        oligo_seq_index = 3  # 1-based indexing
        valid_namespace = argparse.Namespace(
            input=csv_path,
            output=EXAMPLE_OUTPUT_PATH,
            forward_primer="",
            reverse_primer="",
            reverse_complement_flag=False,
            skip_n_rows=3,
            name_header=None,
            name_index=oligo_seq_name_index,
            sequence_index=oligo_seq_index,
            sequence_header=None,
            verbose=False,
        )
        valid_namespace_with_headers = argparse.Namespace(
            input=csv_path,
            output=EXAMPLE_OUTPUT_PATH,
            forward_primer="",
            reverse_primer="",
            reverse_complement_flag=False,
            skip_n_rows=2,
            name_header=oligo_seq_name_header,
            name_index=None,
            sequence_header=oligo_seq_header,
            sequence_index=None,
            verbose=False,
        )
        return ConfigData(
            csv_path=csv_path,
            oligo_seq_name_header=oligo_seq_name_header,
            oligo_seq_name_index=oligo_seq_name_index,
            oligo_seq_header=oligo_seq_header,
            oligo_seq_index=oligo_seq_index,
            valid_namespace=valid_namespace,
            valid_namespace_with_headers=valid_namespace_with_headers,
        )


# TESTS


def test_validate__with_valid_namespace(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()


def test_validate__with_valid_namespace_with_headers(config):
    namespace = config.valid_namespace_with_headers
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()


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
    namespace.input = config.csv_path
    namespace.output = config.csv_path
    args_cleaner = ArgsCleaner(namespace)
    with pytest.raises(ValidationError):
        args_cleaner.validate()


def test_validate_forward_primer(config):
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner._validate_forward_primer()


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


def test_get_clean_input(config):
    namespace = config.valid_namespace
    expected_input = config.csv_path
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_input = args_cleaner.get_clean_input()
    assert expected_input == actual_input


def test_get_clean_skip_n_rows(config):
    expected_skip_n_rows = config.valid_namespace.skip_n_rows
    namespace = config.valid_namespace
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_skip_n_rows = args_cleaner.get_clean_skip_n_rows()
    assert expected_skip_n_rows == actual_skip_n_rows


def test_get_clean_skip_n_rows__with_headers(config):
    expected_skip_n_rows = config.valid_namespace_with_headers.skip_n_rows + 1
    namespace = config.valid_namespace_with_headers
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_skip_n_rows = args_cleaner.get_clean_skip_n_rows()
    assert expected_skip_n_rows == actual_skip_n_rows


def test_get_clean_output__with_specific_output_that_does_exist(config, tmp_path):
    expected_output = tmp_path / "foo.csv"
    expected_output.touch()
    namespace = config.valid_namespace
    namespace.output = expected_output
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_output = args_cleaner.get_clean_output()
    assert expected_output == actual_output


def test_get_clean_output__with_specific_output_that_doesnt_exist(config, tmp_path):
    expected_output = tmp_path / "foo.csv"
    namespace = config.valid_namespace
    namespace.output = expected_output
    args_cleaner = ArgsCleaner(namespace)
    args_cleaner.validate()
    actual_output = args_cleaner.get_clean_output()
    assert expected_output == actual_output


def test_get_clean_output__with_specific_output_dir(config):
    expected_output = (
        config.csv_path.parent / f"{config.csv_path.stem}.out{config.csv_path.suffix}"
    )
    namespace = config.valid_namespace
    namespace.output = config.csv_path.parent
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
