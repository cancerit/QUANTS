import pytest
from shutil import rmtree
import datetime
from pathlib import Path

from src.args import _clean
from src import exceptions as exc
from src import constants as const

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


@pytest.mark.parametrize(
    "index, is_1_indexed, expected",
    [
        # Testing 1-indexed input
        (1, True, 1),
        (2, True, 2),
        (None, True, None),
        # Testing 0-indexed input
        (0, False, 0),
        (1, False, 1),
        (None, False, None),
    ],
)
def test_clean_index_valid_cases(index, is_1_indexed, expected):
    # When
    actual = _clean.clean_index(index, is_1_indexed)

    # Then
    assert actual == expected


@pytest.mark.parametrize(
    "index, is_1_indexed",
    [
        # Testing 1-indexed input
        (0, True),
        (-1, True),
        # Testing 0-indexed input
        (-1, False),
    ],
)
def test_clean_index_invalid_cases(index, is_1_indexed):
    # When
    with pytest.raises(exc.ValidationError) as e:
        _clean.clean_index(index, is_1_indexed)


@pytest.mark.parametrize("delimiter", ["\t", ",", None])
def test_clean_input_delimiter_valid(delimiter):
    # Given
    expected = delimiter

    # When
    actual = _clean.clean_input_delimiter(delimiter)

    # Then
    assert actual == expected


# Testing for invalid delimiters
@pytest.mark.parametrize("delimiter", [";", ":", "|", " "])
def test_clean_input_delimiter_invalid(delimiter):
    # When
    with pytest.raises(exc.ValidationError):
        _clean.clean_input_delimiter(delimiter)


@pytest.mark.parametrize("delimiter, expected", [(None, ","), ("\t", "\t"), (",", ",")])
def test_clean_cast_output_delimiter_valid(delimiter, expected):
    # When
    actual = _clean.clean_output_delimiter(delimiter)

    # Then
    assert actual == expected


@pytest.mark.parametrize("forbidden_delimiter", [";", ":", "|", " "])
def test_clean_cast_output_delimiter_invalid(forbidden_delimiter):
    # When
    with pytest.raises(exc.ValidationError):
        _clean.clean_output_delimiter(forbidden_delimiter)


@pytest.mark.parametrize(
    "reheader_mapping, clean_column_order, mode, append, expected",
    [
        (
            {"a": "x", "b": "y", "c": "z"},
            ["a", "b", "c"],
            const.SUBCOMMAND__COLUMN_INDICES,
            False,
            {"a": "x", "b": "y", "c": "z"},
        ),
        (
            {"a": "x", "b": "y", "c": "z"},
            ["a", "b", "d"],
            const.SUBCOMMAND__COLUMN_INDICES,
            False,
            None,
        ),
        (
            {"a": "x", "b": "y", "c": "z"},
            ["a", "b", "c"],
            "other_mode",
            True,
            {"a": "x", "b": "y", "c": "z"},
        ),
        (
            {"a": "x", "b": "y", "c": "z"},
            ["a", "b", "d"],
            "other_mode",
            True,
            None,
        ),
        # Add more test cases as needed
    ],
)
def test_clean_reheader__must_be_complete(
    reheader_mapping, clean_column_order, mode, append, expected
):
    # When & Then
    if expected is None:
        with pytest.raises(exc.ValidationError):
            _clean.clean_reheader(
                reheader_mapping,
                clean_column_order,
                mode=mode,
                append=append,
            )
    else:
        # When
        actual = _clean.clean_reheader(
            reheader_mapping,
            clean_column_order,
            mode=mode,
            append=append,
        )

        # Then
        assert actual == expected


@pytest.mark.parametrize(
    "reheader_mapping, clean_column_order, mode, append, expected",
    [
        (
            {"a": "x", "b": "y", "c": "z"},
            ["a", "b", "c"],
            "other_mode",
            False,
            {"a": "x", "b": "y", "c": "z"},
        ),
        (
            {"a": "x", "b": "y", "c": "z"},
            ["d", "e", "f"],
            "other_mode",
            False,
            None,
        ),
    ],
)
def test_clean_reheader__partial_overlap(
    reheader_mapping, clean_column_order, mode, append, expected
):
    # When & Then
    if expected is None:
        with pytest.raises(exc.ValidationError):
            _clean.clean_reheader(
                reheader_mapping,
                clean_column_order,
                mode=mode,
                append=append,
            )
    else:
        # When
        actual = _clean.clean_reheader(
            reheader_mapping,
            clean_column_order,
            mode=mode,
            append=append,
        )

        # Then
        assert actual == expected


def test_InputFile_clean(input_file_setup):
    # Given
    input_file = input_file_setup

    # When
    actual = _clean.InputFile(input_file).clean

    # Then
    assert actual == input_file

    # Finally
    input_file.unlink()
    with pytest.raises(exc.ValidationError):
        _clean.InputFile(input_file).clean


def test_OutputFile__with_a_file_path(input_file_setup, example_dir_setup):
    # Given
    input_file = input_file_setup
    output_file = example_dir_setup / "output_file.txt"
    expected = output_file

    # When
    actual = _clean.OutputFile(input_file, output_file).clean

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
    actual = _clean.OutputFile(input_file, output_file).clean

    # Then
    assert output_file.exists()
    assert actual == expected


def test_OutputFile__with_a_dir_path(input_file_setup, example_dir_setup):
    # Given
    input_file = input_file_setup
    output_dir = example_dir_setup
    expected = output_dir / "input_file.txt"

    # When
    actual = _clean.OutputFile(input_file, output_dir).clean

    # Then
    assert actual == expected

    # Finally
    rmtree(output_dir.parent)
    with pytest.raises(exc.ValidationError):
        _clean.OutputFile(input_file, output_dir).clean


def test_OutputFile__without_a_path_specified(input_file_setup):
    # Given
    input_file = input_file_setup
    expected = input_file

    # When
    actual = _clean.OutputFile(input_file, None).clean

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
    actual = _clean.SummaryFile(input_file, summary_file).clean

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
    actual = _clean.SummaryFile(input_file, summary_file).clean

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
    actual = _clean.SummaryFile(input_file, summary_dir).clean

    # Then
    assert actual == expected


def test_SummaryFile__without_a_path_specified(input_file_setup, fixed_datetime):
    # Given
    input_file = input_file_setup
    expected_name = f"{input_file.stem}.summary.{FORMATTED_ARBITRARY_DATETIME}.json"
    expected = input_file.parent / expected_name

    # When
    actual = _clean.SummaryFile(input_file, None).clean

    # Then
    assert actual == expected
