import typing as t
import datetime

if t.TYPE_CHECKING:
    from pathlib import Path

from src.args.io import (
    finalise_output_file,
)
from src.args import validate
from src import exceptions
from src import constants as const


class InputFile:
    """
    Validates an input file.

    A clean input file is a file that exists and is readable.
    """

    def __init__(self, input_file: "Path"):
        self._input_file: "Path" = input_file

    @property
    def clean(self) -> "Path":
        return validate.assert_valid_input_file(self._input_file)


class OutputFile:
    """
    Validates an output file, inferring it from the input file if necessary.

    A clean output file is a file that may not exist but whose parent directory
    is writable.

    Special conditions:
    - If the output file is None, the input file is returned as the clean output file.
    - If the output file is an existing file, it is returned as the clean output file.
    - If the output file is a non-existant file, it is returned as the clean output file.
    - If the output file is an existing directory, that directory and input
        filename are concatenated as clean output file.
    """

    def __init__(self, input_file: "Path", output_file: t.Optional["Path"]):
        self._input_file: "InputFile" = InputFile(input_file)
        self._output_file: t.Optional["Path"] = output_file

    @property
    def clean(self) -> "Path":
        clean_input_file = self._input_file.clean
        output_file = finalise_output_file(clean_input_file, self._output_file)
        return validate.assert_valid_output_file(output_file)


class SummaryFile:
    """
    Validates a summary file, inferring it from the input file if necessary.

    If the summary file is inferred from the input file, it has the following
    format: '<input_file>.summary.<date>.json'

    A clean summary file is a file that may not exist but whose parent directory
    is writable.

    Special conditions:
    - If the summary file is None, the input file is returned as the clean summary file.
    - If the summary file is an existing file, it is returned as the clean summary file.
    - If the summary file is a non-existant file, it is returned as the clean summary file.
    - If the summary file is an existing directory, that directory and input
        filename are concatenated as clean summary file.
    """

    def __init__(self, input_file: "Path", summary_file: t.Optional["Path"]):
        self._input_file: "InputFile" = InputFile(input_file)
        self._summary_file: t.Optional["Path"] = summary_file

    def _summary_name(self, input_path: "Path") -> str:
        now = datetime.datetime.now()
        # Format the date as 2022-12-11T10-09-08
        date_str = now.strftime("%Y-%m-%dT%H-%M-%S")
        new_suffix = ".json"
        new_midfix = f".summary.{date_str}"
        new_name = input_path.stem + new_midfix + new_suffix
        return new_name

    @property
    def clean(self) -> "Path":
        clean_input_file = self._input_file.clean
        # The inferred file is the input file but with the name and suffix
        # changed. This is not going to mean the summary file will use the
        # inferred file, but it might depending on how finalise_output_file
        # evaluates the output file.
        inferred_file = clean_input_file.with_name(self._summary_name(clean_input_file))
        summary_file = finalise_output_file(inferred_file, self._summary_file)
        return validate.assert_valid_output_file(summary_file)


def strict_clean_index(index: int, is_1_indexed: bool = True) -> int:
    if is_1_indexed and index < 1:
        msg = f"Index must be greater than 0, not '{index}' - remember that indices are 1-indexed"
        raise exceptions.ValidationError(msg)
    if not is_1_indexed and index < 0:
        msg = f"Index must be greater than or equal to 0, not '{index}' - remember that indices are 0-indexed"
        raise exceptions.ValidationError(msg)
    return index


def clean_index(index: t.Optional[int], is_1_indexed: bool = True) -> t.Optional[int]:
    if index is None:
        return None
    return strict_clean_index(index, is_1_indexed=is_1_indexed)


def clean_input_delimiter(delimiter: t.Optional[str]) -> t.Optional[str]:
    """
    Validates & cleans the input delimiter. If the delimiter is None, None is returned.
    """
    if delimiter is None:
        return None
    allowed_delimiters = [const.DELIMITER__TAB, const.DELIMITER__COMMA]
    if delimiter not in allowed_delimiters:
        msg = f"Output file delimiter must be a tab or comma, not '{delimiter}'"
        raise exceptions.ValidationError(msg)
    return delimiter


def clean_output_delimiter(delimiter: t.Optional[str], default=",") -> str:
    """
    Validates & cleans the output delimiter. If the delimiter is None, the default is returned.
    """
    allowed_delimiters = [const.DELIMITER__TAB, const.DELIMITER__COMMA]
    if delimiter is None:
        clean_delimiter = default
    else:
        clean_delimiter = delimiter
    if clean_delimiter not in allowed_delimiters:
        msg = f"Output file delimiter must be a tab or comma, not '{delimiter}'"
        raise exceptions.ValidationError(msg)
    return clean_delimiter
