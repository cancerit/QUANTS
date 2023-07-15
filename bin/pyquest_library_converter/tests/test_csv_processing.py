import typing as t
from pathlib import Path
import csv

import pandas as pd
import pytest

from pyquest_library_converter import main
from src.args.args_parsing import get_argparser
from src.args.args_cleaner import ArgsCleaner
from src import constants as const


# CONSTANTS
# EXAMPLE_DATA__SEQUENCE = "AATGATACGGCGACCACCGATCCTGCGCCTTCTCTCCTCCTCCTCCACACTCCAGGCTGGACCTGTACCGAGCCTCGGGTAAATTTGAGCTTCTTGATAGAATTCTTCCCAAACTCCGAGCAACCAACCACAAAGTGCTGCTGTTCTGTCAGATGACTTCCCTCATGACCATCATGGAAGATTACTTTGCGTATCGCGGCTTTAAATACCTCAGGCTTGATGGTGAGTATGAGCCAGTGAGGCGTTTCTTACAGGGTTTTGTTGTTGTGGCTCGTATGCCGTCTTCTGCTTG"
EXAMPLE_DATA__SEQUENCE = "AATTCCGGA"
EXAMPLE_DATA__NAME = "ENST00000344626.10.ENSG00000127616.20_chr19:11027766_1del"
EXAMPE_HEADER__NAME = "name"
EXAMPE_HEADER__SEQUENCE = "sequence"

# HELPERS

# FIXTURES


@pytest.fixture
def get_main_kwargs():
    def _get_main_kwargs(
        input_file: t.Union[str, Path],
        output_file: t.Union[str, Path],
        update_kwargs: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Dict[str, t.Any]:
        default_kwargs = {
            "skip_n_rows": 0,
            "verbose": False,
            "forward_primer": "",
            "reverse_primer": "",
            "name_index": 1,  # 1-based indexing
            "sequence_index": 2,  # 1-based indexing
            "reverse_complement_flag": False,
        }
        kwargs = default_kwargs.copy()
        if update_kwargs is not None:
            kwargs.update(update_kwargs)
        kwargs["input_file"] = input_file
        kwargs["output_file"] = output_file
        return kwargs

    yield _get_main_kwargs


@pytest.fixture
def get_cmd():
    """Return a string of the command to run."""

    def _get_cmd(main_kwargs: t.Dict[str, t.Any]) -> str:
        input_file = main_kwargs["input_file"]
        output_file = main_kwargs["output_file"]
        # USAGE: [-v] [--forward FORWARD_PRIMER] [--reverse REVERSE_PRIMER] [--skip SKIP_N_ROWS] [--revcomp] (-n NAME_HEADER | -N NAME_INDEX) (-s SEQUENCE_HEADER | -S SEQUENCE_INDEX) input output
        cmd = f"{input_file} {output_file}"
        if main_kwargs["verbose"]:
            cmd += " -v"
        if main_kwargs["forward_primer"]:
            cmd += f" --forward {main_kwargs['forward_primer']}"
        if main_kwargs["reverse_primer"]:
            cmd += f" --reverse {main_kwargs['reverse_primer']}"
        if "skip_n_rows" in main_kwargs:  # skip_n_rows can return 0
            cmd += f" --skip {main_kwargs['skip_n_rows']}"
        if main_kwargs["reverse_complement_flag"]:
            cmd += f" --revcomp"
        if "name_index" in main_kwargs:  # name_index can return 0
            cmd += f" -N {main_kwargs['name_index']}"
        if "sequence_index" in main_kwargs:  # sequence_index can return 0
            cmd += f" -S {main_kwargs['sequence_index']}"
        return cmd

    yield _get_cmd


@pytest.fixture
def get_arg_cleaner(get_cmd):
    def _get_arg_cleaner(main_kwargs: t.Dict[str, t.Any]) -> ArgsCleaner:
        parser = get_argparser()
        cmd = get_cmd(main_kwargs)
        namespace = parser.parse_args(cmd.split())
        arg_cleaner = ArgsCleaner(namespace)
        return arg_cleaner

    yield _get_arg_cleaner


@pytest.fixture
def make_csv_file(tmp_path):
    """Create a csv file for testing."""
    tmp_csv = tmp_path / "test.csv"

    def _make_csv_file(csv_file_contents: t.List[t.List[t.Any]], delimiter=",") -> Path:
        with open(tmp_csv, "w") as f:
            writer = csv.writer(f, delimiter=delimiter)
            for row in csv_file_contents:
                safe_row = [str(x) for x in row]
                writer.writerow(safe_row)
        return tmp_csv

    yield _make_csv_file


@pytest.fixture
def read_csv_file():
    """Read a csv file for testing."""

    def _read_csv_file(csv_file_path: Path, delimiter: t.Optional[str] = None):
        if delimiter is None:
            delimiter = const._OUTPUT_DELIMITER
        df = pd.read_csv(str(csv_file_path), delimiter=delimiter)
        return df

    yield _read_csv_file


# TESTS


def test_arg_cleaner_args_vs_main_kwargs(
    make_csv_file, get_arg_cleaner, tmp_path, get_main_kwargs
):
    # Setup data
    input_data = [
        [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
        [EXAMPLE_DATA__NAME, EXAMPLE_DATA__SEQUENCE],
    ]

    # Setup main_kwargs
    input_file = make_csv_file(input_data)
    output_file = tmp_path / "test.out.csv"
    main_kwargs = get_main_kwargs(input_file, output_file)

    # Setup arg_cleaner args
    arg_cleaner: ArgsCleaner = get_arg_cleaner(main_kwargs)
    arg_cleaner.validate()
    arg_cleaner_args = {
        "input_file": arg_cleaner.get_clean_input(),
        "skip_n_rows": arg_cleaner.get_clean_skip_n_rows(),
        "output_file": arg_cleaner.get_clean_output(),
        "verbose": arg_cleaner.get_clean_verbose(),
        "forward_primer": arg_cleaner.get_clean_forward_primer(),
        "reverse_primer": arg_cleaner.get_clean_reverse_primer(),
        "name_index": arg_cleaner.get_clean_name_index(),
        "sequence_index": arg_cleaner.get_clean_sequence_index(),
        "reverse_complement_flag": arg_cleaner.get_clean_reverse_complement_flag(),
    }

    assert main_kwargs == arg_cleaner_args


@pytest.mark.parametrize("use_arg_cleaner", [True, False])
def test_main__with_upper_case_sequences(
    make_csv_file,
    read_csv_file,
    tmp_path,
    get_main_kwargs,
    get_arg_cleaner,
    use_arg_cleaner,
):
    """Test that sequences with upper case letters are converted to lower case."""
    # Setup data
    input_data = [
        [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
        [EXAMPLE_DATA__NAME, EXAMPLE_DATA__SEQUENCE.upper()],
    ]
    output_data = [
        # Header row
        [
            const._OUTPUT_HEADER__ID,
            const._OUTPUT_HEADER__NAME,
            const._OUTPUT_HEADER__SEQUENCE,
        ],
        # Data rows
        [1, EXAMPLE_DATA__NAME, EXAMPLE_DATA__SEQUENCE.upper()],
    ]

    # Given
    input_file = make_csv_file(input_data)
    # new_in_file = Path.cwd() / "test.in.csv"
    # new_in_file.write_text(input_file.read_text())  # TODO REMOVE
    output_file = tmp_path / "test.out.csv"
    main_kwargs = get_main_kwargs(input_file, output_file)
    main_kwargs["skip_n_rows"] = 1
    expected_df = pd.DataFrame(output_data[1:], columns=output_data[0])

    # When: differing execution strategies
    if use_arg_cleaner:
        # Mimics command line execution
        arg_cleaner: ArgsCleaner = get_arg_cleaner(main_kwargs)
        arg_cleaner.validate()
        main(**arg_cleaner.to_clean_dict())
    else:
        # Directly call main
        main(**main_kwargs)

    # When
    actual_df = read_csv_file(output_file)

    # Then
    pd.testing.assert_frame_equal(actual_df, expected_df)
    # new_out_file = Path.cwd() / "test.out.csv"
    # new_out_file.write_text(output_file.read_text())  # TODO REMOVE
