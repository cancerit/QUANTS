import typing as t
import pytest
import os
import tempfile
from pathlib import Path
import shutil

from src.args import _validate

from src import exceptions as exc

# CONSTANTS
FILE_SYMBOL = "file"
DIR_SYMBOL = "dir"


VALID_INPUT_FILE_PARAMS = [
    pytest.param(
        (FILE_SYMBOL, 0o777, False),
        id="valid input file",
    ),
    pytest.param(
        (FILE_SYMBOL, 0o111, True),
        id="input file without read permissions",
    ),
    pytest.param(
        (DIR_SYMBOL, 0o777, True),
        id="input path is a directory",
    ),
    pytest.param(
        (None, None, True),
        id="input file doesn't exist",
    ),
]

VALID_OUTPUT_FILE_PARAMS = [
    pytest.param(
        (DIR_SYMBOL, 0o777, False),
        id="valid output file",
    ),
    pytest.param(
        (DIR_SYMBOL, 0o555, True),
        id="output file directory without write permissions",
    ),
    pytest.param(
        (None, None, True),
        id="output file directory doesn't exist",
    ),
]


# FIXTURES


@pytest.fixture()
def input_file_setup(request):
    # Setup
    path_type, permissions, should_throw = request.param

    # Create a temporary directory for the tests
    temp_dir = tempfile.mkdtemp()
    path = Path(temp_dir) / "file.txt"

    if path_type == FILE_SYMBOL:
        with open(path, "w") as f:
            text = "example text"
            f.write(text)
        os.chmod(path, permissions)
    elif path_type == DIR_SYMBOL:
        path.mkdir()

    yield path, should_throw

    # Teardown - remove the temporary directory
    shutil.rmtree(temp_dir)


@pytest.fixture()
def output_file_setup(request):
    # Setup
    path_type, permissions, should_throw = request.param

    # Create a temporary directory for the tests
    temp_dir = tempfile.mkdtemp()
    path = Path(temp_dir) / "dir" / "file.txt"

    if path_type == DIR_SYMBOL:
        path.parent.mkdir()
        os.chmod(path.parent, permissions)

    yield path, should_throw

    # Teardown - remove the temporary directory
    shutil.rmtree(temp_dir)


# TESTS


@pytest.mark.parametrize("input_file_setup", VALID_INPUT_FILE_PARAMS, indirect=True)
def test_assert_valid_input_file(input_file_setup):
    # Given
    input_file, should_throw = input_file_setup
    expected = input_file

    # When
    if should_throw:
        with pytest.raises(exc.ValidationError):
            _validate.assert_valid_input_file(input_file)
    else:
        # When and Then
        actual = _validate.assert_valid_input_file(input_file)
        assert actual == expected


@pytest.mark.parametrize("output_file_setup", VALID_OUTPUT_FILE_PARAMS, indirect=True)
def test_assert_valid_output_file(output_file_setup):
    # Given
    output_file, should_throw = output_file_setup
    expected = output_file

    # When
    if should_throw:
        with pytest.raises(exc.ValidationError):
            _validate.assert_valid_output_file(output_file)
    else:
        # When and Then
        actual = _validate.assert_valid_output_file(output_file)
        assert actual == expected
