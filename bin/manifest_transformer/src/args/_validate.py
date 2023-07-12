import typing as t

if t.TYPE_CHECKING:
    from pathlib import Path

from src.args._io import (
    check_write_permissions,
    check_read_permissions,
    check_file_not_empty,
)
from src import exceptions as exc


def assert_valid_input_file(input_file: "Path") -> "Path":
    if not input_file.exists():
        raise exc.ValidationError(f"Input file {input_file!r} does not exist.")
    if not input_file.is_file():
        raise exc.ValidationError(f"Input file {input_file!r} is not a file.")
    check_read_permissions(input_file)
    check_file_not_empty(input_file)
    return input_file


def assert_valid_output_file(output_file: "Path") -> "Path":
    """
    Output file should correspond to a file but it does not have to exist yet.

    If it does exist, it's parent directory must exist and be writable.
    """
    exists = output_file.exists()
    is_dir = output_file.is_dir()  # If a dir does not exist, this will be False
    parent_exists = output_file.parent.exists()

    forbidden_conditions = any(
        [
            is_dir,
            not exists and not parent_exists,
        ]
    )
    if forbidden_conditions:
        msg = f"Output file {output_file!r} must be a file and its parent directory must exist."
        raise exc.ValidationError(msg)

    # We know that output_file is not a directory and its parent directory
    # exists, but it may not exist itself. If it does exist, it must be a file
    # that will be over-written. If it does not exist, it WILL be a file.
    #
    # Hence we need to check that the parent directory is writable.

    validation_candiate = output_file.parent
    check_write_permissions(validation_candiate)
    return output_file
