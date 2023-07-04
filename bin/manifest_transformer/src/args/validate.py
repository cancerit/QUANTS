import typing as t

if t.TYPE_CHECKING:
    from pathlib import Path

from src.args.io import (
    check_write_permissions,
    check_read_permissions,
)
from src import exceptions as exc


def assert_valid_input_file(input_file: "Path") -> "Path":
    if not input_file.exists():
        raise exc.ValidationError(f"Input file {input_file!r} does not exist.")
    if not input_file.is_file():
        raise exc.ValidationError(f"Input file {input_file!r} is not a file.")
    check_read_permissions(input_file)
    return input_file


def assert_valid_output_file(output_file: "Path") -> "Path":
    if output_file.parent.exists():
        check_write_permissions(output_file.parent)
    else:
        msg = f"Output file {output_file!r} directory does not exist."
        raise exc.ValidationError(msg)
    return output_file
