import typing as t
from pathlib import Path
import csv

import pandas as pd
import pytest

from pyquest_library_converter import (
    main,
)

from src import constants as const


# CONSTANTS
EXAMPLE_DATA__SEQUENCE = "AATGATACGGCGACCACCGATCCTGCGCCTTCTCTCCTCCTCCTCCACACTCCAGGCTGGACCTGTACCGAGCCTCGGGTAAATTTGAGCTTCTTGATAGAATTCTTCCCAAACTCCGAGCAACCAACCACAAAGTGCTGCTGTTCTGTCAGATGACTTCCCTCATGACCATCATGGAAGATTACTTTGCGTATCGCGGCTTTAAATACCTCAGGCTTGATGGTGAGTATGAGCCAGTGAGGCGTTTCTTACAGGGTTTTGTTGTTGTGGCTCGTATGCCGTCTTCTGCTTG"
EXAMPLE_DATA__NAME = "ENST00000344626.10.ENSG00000127616.20_chr19:11027766_1del"
EXAMPE_HEADER__NAME = "name"
EXAMPE_HEADER__SEQUENCE = "sequence"


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

    def _read_csv_file(csv_file_path: Path, delimiter=","):
        df = pd.read_csv(str(csv_file_path), delimiter=delimiter)
        return df

    yield _read_csv_file


# TESTS


@pytest.mark.xfail(reason="TODO: Implement")
def test_main__with_upper_case_sequences(
    make_csv_file, read_csv_file, tmp_path, get_main_kwargs
):
    """Test that sequences with upper case letters are converted to lower case."""
    # Setup data
    input_data = [
        [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
        [EXAMPLE_DATA__NAME, EXAMPLE_DATA__SEQUENCE.upper()],
    ]
    output_data = [
        [const._OUTPUT_HEADER__NAME, const._OUTPUT_HEADER__SEQUENCE],
        [EXAMPLE_DATA__NAME, EXAMPLE_DATA__SEQUENCE.upper()],
    ]

    # Given
    input_file = make_csv_file(input_data)
    print("\n", read_csv_file(input_file))
    output_file = tmp_path / "test.out.csv"
    main_kwargs = get_main_kwargs(input_file, output_file)
    expected_df = pd.DataFrame(output_data[1:], columns=output_data[0])

    # When
    main(**main_kwargs)
    actual_df = read_csv_file(output_file)

    # Then
    pd.testing.assert_frame_equal(actual_df, expected_df)
