import os
from pathlib import Path
import typing as t

from src import exceptions as exc


def check_write_permissions(path: Path) -> None:
    if not os.access(path, os.W_OK):
        raise exc.ValidationError(f"{path!r} is not writable.")


def check_read_permissions(path: Path) -> None:
    if not os.access(path, os.R_OK):
        raise exc.ValidationError(f"{path!r} is not readable.")


def check_file_not_empty(path: Path) -> None:
    if not path.exists():
        msg = f"The file '{str(path)}' does not exist."
        raise exc.ValidationError()
    if not path.is_file():
        msg = f"The file '{str(path)}' is not a file."
        raise exc.ValidationError(msg)
    with open(path, "r") as file:
        contents = file.read()
        if not contents or contents.isspace():
            msg = f"The file '{str(path)}' is empty or contains only whitespace."
            raise exc.ValidationError(msg)


def finalise_output_file(input_path: Path, output_path: t.Optional[Path]) -> Path:
    """
    Determine what the output file path should be given a user specified input
    and output path.

    Default to overwriting input file when no output path is specified. Also
    handles the case where the output path is a directory.
    """

    if output_path is None:
        # Default to overwriting input file when no output path is specified
        finalised = input_path
    elif output_path.exists() and output_path.is_file():
        finalised = output_path
    elif output_path.exists() and output_path.is_dir():
        finalised = output_path / input_path.name
    elif output_path.parent.exists() and not output_path.exists():
        finalised = output_path
    else:
        msg = f"Output path {output_path!r} must exist or if it does not, its parent must exist."
        raise exc.ValidationError(msg)
    return finalised
