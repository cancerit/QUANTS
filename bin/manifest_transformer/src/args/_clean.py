import typing as t
import datetime
from pathlib import Path


from src.args._io import (
    finalise_output_file,
)
from src.args import _validate
from src import exceptions
from src import constants as const


class InputFile:
    """
    Validates an input file.

    A clean input file is a file that exists and is readable.
    """

    def __init__(self, input_file: t.Union["Path", str]):
        try:
            self._input_file: "Path" = Path(input_file)
        except TypeError:
            msg = f"Input file must be a string or Path, not {type(input_file)}"
            raise exceptions.ValidationError(msg) from None

    @property
    def clean(self) -> "Path":
        return _validate.assert_valid_input_file(self._input_file)


class OutputFile:
    """
    Validates an output file, inferring it from the input file if necessary.

    A clean output file is a file that may not exist but whose parent directory
    is writable.

    Special conditions:
    - If the output file is None, a ValidationError is raised.
    - If the output file is equal to the input file, a ValidationError is raised.
    - If the output file is an existing file, it is returned as the clean output file.
    - If the output file is a non-existant file, it is returned as the clean output file.
    - If the output file is an existing directory, that directory and input
        filename are concatenated as clean output file.
    """

    def __init__(
        self,
        input_file: t.Union["Path", str],
        output_file: t.Union["Path", str],
    ):
        self._input_file: "InputFile" = InputFile(input_file)
        self._output_file: t.Optional["Path"] = (
            Path(output_file) if output_file is not None else None
        )

    @property
    def clean(self) -> "Path":
        if self._output_file is None:
            msg = f"Output file is not optional, but was not provided: got {self._output_file!r}"
            raise exceptions.ValidationError(msg)
        clean_input_file = self._input_file.clean
        output_file = finalise_output_file(clean_input_file, self._output_file)
        if output_file == clean_input_file:
            msg = f"Output file cannot be the same as the input file: got {str(output_file)!r}"
            raise exceptions.ValidationError(msg)
        return _validate.assert_valid_output_file(output_file)


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

    def __init__(
        self,
        input_file: "t.Union[str, Path]",
        summary_file: t.Optional[t.Union["Path", str]],
    ):
        self._input_file: "InputFile" = InputFile(input_file)
        self._summary_file: t.Optional["Path"] = (
            Path(summary_file) if summary_file is not None else None
        )

    def _summary_name(self, input_path: "Path") -> str:
        now = datetime.datetime.now()
        # Format the date as 2022-12-11T10-09-08
        date_str = now.strftime("%Y-%m-%dT%H-%M-%S")
        new_suffix = ".json"
        new_midfix = f".summary.{date_str}"
        new_name = input_path.stem + new_midfix + new_suffix
        return new_name

    @property
    def clean(self) -> t.Optional["Path"]:
        clean_input_file = self._input_file.clean
        # The inferred file is the input file but with the name and suffix
        # changed. This is not going to mean the summary file will use the
        # inferred file, but it might depending on how finalise_output_file
        # evaluates the output file.
        if self._summary_file is None:
            return None
        inferred_file = clean_input_file.with_name(self._summary_name(clean_input_file))
        summary_file = finalise_output_file(inferred_file, self._summary_file)
        if summary_file == clean_input_file:
            msg = f"Summary file cannot be the same as the input file: got {str(summary_file)!r}"
            raise exceptions.ValidationError(msg)
        return _validate.assert_valid_output_file(summary_file)


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


def clean_reheader(
    reheader_mapping: t.Dict[t.Any, str],
    clean_column_order: t.Iterable[t.Any],
    mode: str,
    append: bool,
) -> t.Dict[t.Any, str]:
    if mode == const.SUBCOMMAND__COLUMN_NAMES and append:
        msg_not_valid = f"You cannot do reheader-append while in {const.SUBCOMMAND__COLUMN_NAMES!r} mode."
        raise exceptions.ValidationError(msg_not_valid)
    elif mode not in {const.SUBCOMMAND__COLUMN_INDICES, const.SUBCOMMAND__COLUMN_NAMES}:
        msg_not_valid = f"Mode must be one of {const.SUBCOMMAND__COLUMN_INDICES!r} or {const.SUBCOMMAND__COLUMN_NAMES!r}, not {mode!r}"
        raise NotImplementedError(msg_not_valid)
    return _clean_reheader(reheader_mapping, clean_column_order, mode, append)


def _clean_reheader(
    reheader_mapping: t.Dict[t.Any, str],
    clean_column_order: t.Iterable[t.Any],
    mode: str,
    append: bool,
) -> t.Dict[t.Any, str]:
    must_be_complete = (mode == const.SUBCOMMAND__COLUMN_INDICES) or append == True
    reheader_start_values = set(reheader_mapping.keys())
    clean_column_order_ = set(clean_column_order)

    # Check that the reheader mapping overlaps with the column order
    complete_overlap = reheader_start_values == clean_column_order_

    if must_be_complete and not complete_overlap:
        # A complete overlap is required if must_be_complete is True
        detail_got = ", ".join(
            f"{str(elem)!r}" for elem in sorted(reheader_start_values)
        )
        missing_keys = reheader_start_values.symmetric_difference(clean_column_order_)
        detail_missing = ", ".join(f"{str(elem)!r}" for elem in sorted(missing_keys))
        msg = f"Reheader mapping must be a subset of the sum of required+optional columns: got {detail_got}, missing {detail_missing}."
        raise exceptions.ValidationError(msg)
    # Catch any reheader_start_values that are not in the column order
    elif not reheader_start_values.issubset(clean_column_order_):
        detail_got = ", ".join(
            f"{str(elem)!r}" for elem in sorted(reheader_start_values)
        )

        detail_undocumented = ", ".join(
            f"{str(elem)!r}"
            for elem in sorted(reheader_start_values - clean_column_order_)
        )
        detail_sum = ", ".join(f"{str(elem)!r}" for elem in sorted(clean_column_order_))
        msg = f"Reheader mapping has unique members not found in the sum of required+optional columns: reheader keys {detail_got}; unexpected keys {detail_undocumented}; required+optional keys {detail_sum}."
        raise exceptions.ValidationError(msg)
    else:
        return reheader_mapping
