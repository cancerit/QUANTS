import os
from pathlib import Path

from src import exceptions as exc


def check_write_permissions(path: Path) -> None:
    if not os.access(path, os.W_OK):
        raise exc.ValidationError(f"{path!r} is not writable.")


def check_read_permissions(path: Path) -> None:
    if not os.access(path, os.R_OK):
        raise exc.ValidationError(f"{path!r} is not readable.")
