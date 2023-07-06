import pytest
from shutil import rmtree
import datetime
from pathlib import Path

from src.args import clean
from src import exceptions as exc

# CONSTANTS
ARBITRARY_DATETIME = datetime.datetime(2022, 12, 11, 10, 9, 8)
FORMATTED_ARBITRARY_DATETIME = "2022-12-11T10-09-08"

# FIXTURES


@pytest.fixture
def fixed_datetime(monkeypatch):
    class MyDateTime:
        @classmethod
        def now(cls):
            return ARBITRARY_DATETIME

    monkeypatch.setattr(datetime, "datetime", MyDateTime)


@pytest.fixture()
def input_file_setup(tmp_path):
    input_file = tmp_path / "input_file.txt"
    input_file.touch()
    yield input_file


@pytest.fixture()
def example_dir_setup(tmp_path):
    example_dir = tmp_path / "dir"
    example_dir.mkdir()
    yield example_dir


# TESTS


def test_InputFile_clean(input_file_setup):
    # Given
    input_file = input_file_setup

    # When
    actual = clean.InputFile(input_file).clean

    # Then
    assert actual == input_file

    # Finally
    input_file.unlink()
    with pytest.raises(exc.ValidationError):
        clean.InputFile(input_file).clean


def test_OutputFile__with_a_file_path(input_file_setup, example_dir_setup):
    # Given
    input_file = input_file_setup
    output_file = example_dir_setup / "output_file.txt"
    expected = output_file

    # When
    actual = clean.OutputFile(input_file, output_file).clean

    # Then
    assert not output_file.exists()
    assert actual == expected


def test_OutputFile__with_a_prexisting_file_path(input_file_setup, example_dir_setup):
    # Given
    input_file = input_file_setup
    output_file = example_dir_setup / "output_file.txt"
    output_file.touch()
    expected = output_file

    # When
    actual = clean.OutputFile(input_file, output_file).clean

    # Then
    assert output_file.exists()
    assert actual == expected


def test_OutputFile__with_a_dir_path(input_file_setup, example_dir_setup):
    # Given
    input_file = input_file_setup
    output_dir = example_dir_setup
    expected = output_dir / "input_file.txt"

    # When
    actual = clean.OutputFile(input_file, output_dir).clean

    # Then
    assert actual == expected

    # Finally
    rmtree(output_dir.parent)
    with pytest.raises(exc.ValidationError):
        clean.OutputFile(input_file, output_dir).clean


def test_OutputFile__without_a_path_specified(input_file_setup):
    # Given
    input_file = input_file_setup
    expected = input_file

    # When
    actual = clean.OutputFile(input_file, None).clean

    # Then
    assert actual == expected


def test_SummaryFile__with_a_file_path(
    input_file_setup, example_dir_setup, fixed_datetime
):
    # Given
    input_file = input_file_setup
    summary_file = example_dir_setup / "summary_file.json"
    expected_name = "summary_file.json"
    expected = example_dir_setup / expected_name

    # When
    actual = clean.SummaryFile(input_file, summary_file).clean

    # Then
    assert actual == expected


def test_SummaryFile__with_a_preexisting_file_path(
    input_file_setup, example_dir_setup, fixed_datetime
):
    # Given
    input_file = input_file_setup
    summary_file = example_dir_setup / "summary_file.json"
    summary_file.touch()
    expected_name = "summary_file.json"
    expected = example_dir_setup / expected_name

    # When
    actual = clean.SummaryFile(input_file, summary_file).clean

    # Then
    assert actual == expected


def test_SummaryFile__with_a_dir_path(
    input_file_setup, example_dir_setup, fixed_datetime
):
    # Given
    input_file = input_file_setup
    summary_dir = example_dir_setup
    expected_name = f"{input_file.stem}.summary.{FORMATTED_ARBITRARY_DATETIME}.json"
    expected = summary_dir / expected_name

    # When
    actual = clean.SummaryFile(input_file, summary_dir).clean

    # Then
    assert actual == expected


def test_SummaryFile__without_a_path_specified(input_file_setup, fixed_datetime):
    # Given
    input_file = input_file_setup
    expected_name = f"{input_file.stem}.summary.{FORMATTED_ARBITRARY_DATETIME}.json"
    expected = input_file.parent / expected_name

    # When
    actual = clean.SummaryFile(input_file, None).clean

    # Then
    assert actual == expected
