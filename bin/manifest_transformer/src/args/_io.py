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
