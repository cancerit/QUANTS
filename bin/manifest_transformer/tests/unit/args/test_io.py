import typing as t
import pytest
import os
import tempfile
from pathlib import Path

from src import exceptions as exc
from src.args.io import check_write_permissions, check_read_permissions

# CONSTANTS
FILE_SYMBOL = "file"
DIR_SYMBOL = "dir"

# PARAMS
PATH_PARAMS = [
    pytest.param((FILE_SYMBOL, 0o777), id="file with rwx permissions"),
    pytest.param((FILE_SYMBOL, 0o444), id="file with r-- permissions"),
    pytest.param((DIR_SYMBOL, 0o777), id="dir with rwx permissions"),
    pytest.param((DIR_SYMBOL, 0o555), id="dir with r-x permissions"),
]

# FIXTURES


@pytest.fixture()
def path_with_permissions(request):
    path_type, permissions = request.param
    if path_type == FILE_SYMBOL:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            os.chmod(f.name, permissions)
            yield Path(f.name)
        os.remove(f.name)
    elif path_type == DIR_SYMBOL:
        dir_name = tempfile.mkdtemp()
        os.chmod(dir_name, permissions)
        yield Path(dir_name)
        os.rmdir(dir_name)
    else:
        raise ValueError(f"Unknown path type: {path_type}")


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
