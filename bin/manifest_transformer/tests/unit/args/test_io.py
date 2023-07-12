import typing as t
import pytest
import os
import tempfile
from pathlib import Path
import shutil

from src import exceptions as exc
from src.args._io import (
    check_write_permissions,
    check_read_permissions,
    check_file_not_empty,
    finalise_output_file,
)

# CONSTANTS
FILE_SYMBOL = "file"
DIR_SYMBOL = "dir"

EXISTING_FILE = "existing_file"
EXISTING_DIR = "existing_dir"
NON_EXISTING_BUT_PARENT_DIR = "non_existing_but_parent_dir"
NON_EXISTING_NO_PARENT_DIR = "non_existing_no_parent_dir"

ACTION__TOUCH = "touch"
ACTION__WRITE = "write"
ACTION__WRITE_WHITESPACE = "write_whitespace"
ACTION__UNLINK = "unlink"


# PARAMS
PATH_PARAMS = [
    pytest.param((FILE_SYMBOL, 0o777), id="file with rwx permissions"),
    pytest.param((FILE_SYMBOL, 0o111), id="file with --x permissions"),
    pytest.param((DIR_SYMBOL, 0o777), id="dir with rwx permissions"),
    pytest.param((DIR_SYMBOL, 0o555), id="dir with r-x permissions"),
]

FINALISE_OUTPUT_PARAMS = [
    pytest.param(
        (
            Path("input.txt"),
            None,
            None,
            Path("input.txt"),
        ),
        id="output path is None",
    ),
    pytest.param(
        (
            Path("input.txt"),
            Path("output.txt"),
            EXISTING_FILE,
            Path("output.txt"),
        ),
        id="output path is existing file",
    ),
    pytest.param(
        (
            Path("input.txt"),
            Path("output_dir"),
            EXISTING_DIR,
            Path("output_dir/input.txt"),
        ),
        id="output path is existing directory",
    ),
    pytest.param(
        (
            Path("input.txt"),
            Path("output_dir/non_existing.txt"),
            NON_EXISTING_BUT_PARENT_DIR,
            Path("output_dir/non_existing.txt"),
        ),
        id="output path doesn't exist, but parent dir does",
    ),
    pytest.param(
        (
            Path("input.txt"),
            Path("non_existing_output_dir/output.txt"),
            NON_EXISTING_NO_PARENT_DIR,
            None,
        ),
        id="output path and parent dir don't exist",
    ),
]

PARAMS_EMPTY_FILE = [
    # action, content, should_throw
    pytest.param(
        (ACTION__TOUCH, "", True),
        id="touch_file",
    ),
    pytest.param(
        (ACTION__WRITE, "col1,col2,col3\r\na,b,c\r\n", False),
        id="write_file",
    ),
    pytest.param(
        (ACTION__WRITE_WHITESPACE, " ", True),
        id="write_whitespace_file__one_space",
    ),
    pytest.param(
        (ACTION__WRITE_WHITESPACE, " " * 100, True),
        id="write_whitespace_file__hundred_spaces",
    ),
    pytest.param(
        (ACTION__WRITE_WHITESPACE, "\t", True),
        id="write_whitespace_file__one_tab",
    ),
    pytest.param(
        (ACTION__WRITE_WHITESPACE, "\t" * 100, True),
        id="write_whitespace_file__hundred_tabs",
    ),
    pytest.param(
        (ACTION__WRITE_WHITESPACE, "\n", True),
        id="write_whitespace_file__one_newline",
    ),
    pytest.param(
        (ACTION__WRITE_WHITESPACE, "\n" * 100, True),
        id="write_whitespace_file__hundred_newlines",
    ),
    pytest.param(
        (ACTION__WRITE_WHITESPACE, "\r\n", True),
        id="write_whitespace_file__one_crlf",
    ),
    pytest.param(
        (ACTION__WRITE_WHITESPACE, "\r\n" * 100, True),
        id="write_whitespace_file__hundred_crlfs",
    ),
    pytest.param(
        (ACTION__UNLINK, "", True),
        id="unlink_file",
    ),
]

# FIXTURES


@pytest.fixture()
def path_with_permissions(request, tmp_path):
    request.addfinalizer(lambda: shutil.rmtree(tmp_path))
    path_type, permissions = request.param
    if path_type == FILE_SYMBOL:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            os.chmod(f.name, permissions)
            yield Path(f.name)
        os.remove(f.name)
    elif path_type == DIR_SYMBOL:
        dir_name = tmp_path / "temp_dir"
        dir_name.mkdir()
        os.chmod(dir_name, permissions)
        yield Path(dir_name)
        os.chmod(dir_name, 0o755)
    else:
        raise ValueError(f"Unknown path type: {path_type}")


@pytest.fixture()
def path_setup(request, tmp_path) -> t.Generator[t.Tuple[Path, Path, str], None, None]:
    # Setup
    input_path, output_path, file_or_dir, expected = request.param

    # Create a temporary directory for the tests
    temp_dir = tmp_path / "temp_dir"
    temp_dir.mkdir()
    input_path = temp_dir / input_path

    # Create the input file
    with open(input_path, "w") as f:
        f.write("example text")

    # Handle the output path
    if output_path is not None:
        if file_or_dir == EXISTING_FILE:
            # The output path would be overwritten, so create a file
            output_path = temp_dir / output_path
            with open(output_path, "w") as f:
                f.write("example text")
        elif file_or_dir == EXISTING_DIR:
            output_path = temp_dir / output_path
            output_path.mkdir()
        elif file_or_dir == NON_EXISTING_BUT_PARENT_DIR:
            output_path = temp_dir / output_path
            output_path.parent.mkdir()
        elif file_or_dir == NON_EXISTING_NO_PARENT_DIR:
            output_path = temp_dir / output_path

    yield input_path, output_path, expected


@pytest.fixture()
def prepare_empty_file(request, tmp_path):
    (action, string, should_throw) = request.param
    file = tmp_path / "temp_file.txt"
    file.parent.mkdir(exist_ok=True)
    if action == ACTION__TOUCH:
        file.touch()
    elif action == ACTION__WRITE:
        file.write_text(string)
    elif action == ACTION__WRITE_WHITESPACE:
        file.write_text(string)
    elif action == ACTION__UNLINK:
        file.touch()
        file.unlink()
    else:
        raise RuntimeError(f"Unknown action: {action}")

    yield (file, should_throw)


# TESTS


@pytest.mark.parametrize(
    "path_with_permissions",
    PATH_PARAMS,
    indirect=["path_with_permissions"],
)
def test_check_write_permissions(path_with_permissions):
    if os.access(path_with_permissions, os.W_OK):
        # Given dir is writable, so no exception is expected
        check_write_permissions(path_with_permissions)
    else:
        # Given dir is not writable, so an exception is expected
        with pytest.raises(exc.ValidationError):
            check_write_permissions(path_with_permissions)


@pytest.mark.parametrize(
    "path_with_permissions",
    PATH_PARAMS,
    indirect=["path_with_permissions"],
)
def test_check_read_permissions(path_with_permissions):
    if os.access(path_with_permissions, os.R_OK):
        # Given file is readable, so no exception is expected
        check_read_permissions(path_with_permissions)
    else:
        # Given file is not readable, so an exception is expected
        with pytest.raises(exc.ValidationError):
            check_read_permissions(path_with_permissions)


@pytest.mark.parametrize(
    "prepare_empty_file",
    PARAMS_EMPTY_FILE,
    indirect=["prepare_empty_file"],
)
def test_check_file_not_empty(prepare_empty_file):
    # Given
    file, should_throw = prepare_empty_file

    if should_throw:
        # When and then
        with pytest.raises(exc.ValidationError):
            check_file_not_empty(file)
    else:
        # When
        check_file_not_empty(file)

        # Then
        assert True


@pytest.mark.parametrize("path_setup", FINALISE_OUTPUT_PARAMS, indirect=True)
def test_finalise_output_file(path_setup):
    # Given - inputs are set by path_setup
    input_path, output_path, expected = path_setup
    should_not_throw = (
        output_path is None or output_path.exists() or output_path.parent.exists()
    )

    if should_not_throw:
        # When
        actual = finalise_output_file(input_path, output_path)
        relative_actual = actual.relative_to(input_path.parent)

        # Then
        assert relative_actual == expected
    else:
        # When and then
        with pytest.raises(exc.ValidationError):
            finalise_output_file(input_path, output_path)
