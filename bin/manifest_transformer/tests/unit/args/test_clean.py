from unittest import expectedFailure
import pytest
from shutil import rmtree

from src.args import clean
from src import exceptions as exc

# FIXTURES


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
