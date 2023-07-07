# -*- coding: utf-8 -*-
import typing as t
import argparse
import os
from pathlib import Path

from src import constants as const
from src import exceptions as exc

if t.TYPE_CHECKING:
    from src.io import CSVHelper


class ArgsCleaner:
    _ALLOWED_DNA = "ACTG"

    def __init__(self, namespace: argparse.Namespace):
        self._namespace = namespace
        self._parsed_csv = None
        self._validated = False
        self._validated_input = False
        self._csv_helper: "t.Optional[CSVHelper]" = None
        self._header_row_discovered = False
        self._header_row_index = -1

    def _get_arg(self, arg_name: str) -> t.Any:
        if not hasattr(self._namespace, arg_name):
            msg = (
                f"Argument {arg_name!r} no longer has an attribute on the "
                f"{self._namespace!r} object, which suggests "
                "the arg parser has changed."
            )
            raise AttributeError(msg)
        return getattr(self._namespace, arg_name)

    def get_clean_input(self) -> Path:
        self._assert_has_validated_all()
        return self._get_arg(const.ARG_INPUT)

    def get_clean_skip_n_rows(self) -> int:
        self._assert_has_validated_all()
        return self._normailse_skip_n_rows()

    def get_clean_output(self) -> Path:
        self._assert_has_validated_all()
        output: Path = self._normalise_output_to_file()
        return output

    def get_clean_forward_primer(self) -> str:
        self._assert_has_validated_all()
        return self._get_arg(const.ARG_FORWARD_PRIMER)

    def get_clean_reverse_primer(self) -> str:
        self._assert_has_validated_all()
        return self._get_arg(const.ARG_REVERSE_PRIMER)

    def get_clean_verbose(self) -> bool:
        self._assert_has_validated_all()
        return self._get_arg(const.ARG_VERBOSE)

    def get_clean_name_index(self) -> int:
        self._assert_has_validated_all()
        index = self._normailse_header_or_index_to_index(
            header_attr=const.ARG_NAME_HEADER,
            index_attr=const.ARG_NAME_INDEX,
        )
        return index

    def get_clean_sequence_index(self) -> int:
        self._assert_has_validated_all()
        index = self._normailse_header_or_index_to_index(
            header_attr=const.ARG_SEQ_HEADER,
            index_attr=const.ARG_SEQ_INDEX,
        )
        return index

    def get_clean_reverse_complement_flag(self) -> bool:
        self._assert_has_validated_all()
        return self._get_arg(const.ARG_REVERSE_COMPLEMENT_FLAG)

    def validate(self):
        validators = [
            self._validate_codependent_input_args,
            self._validate_output,
            self._validate_forward_primer,
            self._validate_reverse_primer,
            self._validate_name_index,
            self._validate_sequence_index,
            self._validate_reverse_complement_flag,
        ]
        for validator in validators:
            validator()
        self._validated = True
        return

    def _validate_codependent_input_args(self):
        self.__validate_input()
        self.__validate_skip_n_rows()
        self._assert_or_set_csv_helper()
        self._validated_input = True
        return

    def __validate_input(self):
        input_value: Path = self._get_arg(const.ARG_INPUT)
        if not input_value.exists():
            raise exc.ValidationError(f"Input file {input_value!r} does not exist.")
        if not input_value.is_file():
            raise exc.ValidationError(f"Input file {input_value!r} is not a file.")
        self._check_read_permissions(input_value)
        return

    def __validate_skip_n_rows(self):
        skip_n_rows = self._get_arg(const.ARG_SKIP_N_ROWS)
        if skip_n_rows < 0:
            msg = f"Skip n rows {skip_n_rows} must be >= 0."
            raise exc.ValidationError(msg)
        return

    def _validate_output(self):
        output_file: Path = self._normalise_output_to_file()
        if output_file.parent.exists():
            self._check_write_permissions(output_file.parent)
        else:
            msg = f"Output file {output_file!r} directory does not exist."
            raise exc.ValidationError(msg)
        return

    def _validate_sequence_index(self):
        index = self._normailse_header_or_index_to_index(
            header_attr=const.ARG_SEQ_HEADER,
            index_attr=const.ARG_SEQ_INDEX,
        )
        self._assert_valid_column_index(index)
        return

    def _validate_name_index(self):
        index = self._normailse_header_or_index_to_index(
            header_attr=const.ARG_NAME_HEADER,
            index_attr=const.ARG_NAME_INDEX,
        )
        self._assert_valid_column_index(index)
        return

    def _validate_forward_primer(self):
        forward_primer_value: str = self._get_arg(const.ARG_FORWARD_PRIMER)
        allowed_chars = set(self._ALLOWED_DNA.upper())
        self._assert_valid_chars(forward_primer_value, allowed_chars)

    def _validate_reverse_primer(self):
        reverse_primer_value: str = self._get_arg(const.ARG_REVERSE_PRIMER)
        allowed_chars = set(self._ALLOWED_DNA.upper())
        self._assert_valid_chars(reverse_primer_value, allowed_chars)

    def _validate_reverse_complement_flag(self):
        flag = self._get_arg(const.ARG_REVERSE_COMPLEMENT_FLAG)
        if not isinstance(flag, bool):
            msg = f"Reverse complement flag {flag!r} must be a boolean."
            raise exc.ValidationError(msg)
        return

    def _assert_has_validated_all(self, throw=True) -> bool:
        if not self._validated:
            msg = "ArgsCleaner.validate() must be called before accessing cleaned args."
            if throw:
                raise RuntimeError(msg)
            return False
        return True

    def _assert_has_validated_input(self):
        if not self._validated_input:
            msg = (
                "The index cannot be validated before input file " "has been validated."
            )
            raise RuntimeError(msg)

    def _assert_or_set_csv_helper(self):
        file_path: Path = self._get_arg(const.ARG_INPUT)
        skip_n_rows: int = self._get_arg(const.ARG_SKIP_N_ROWS)
        try:
            self._csv_helper = CSVHelper(file_path, skip_n_rows)
        except ValueError as e:
            raise exc.ValidationError(str(e))
        if self._csv_helper.columns_count < 2:
            msg = (
                f"Input file {file_path!r} has {self._csv_helper.columns_count} columns, "
                "but at least 2 are required."
            )
            raise exc.ValidationError(msg)
        return

    def _assert_valid_chars(self, string: str, allowed_chars: t.Set[str]):
        for char in string:
            if char not in allowed_chars:
                msg = (
                    f"Character {char!r} in {string!r} is not in the allowed "
                    f"characters {allowed_chars!r} (case insensitive)."
                )
                raise exc.ValidationError(msg)

    def _assert_valid_column_index(self, index: int):
        """
        Index is 1-indexed.
        """
        self._assert_has_validated_input()
        if not self._validated_input:
            msg = (
                "The index cannot be validated before input file " "has been validated."
            )
            raise RuntimeError(msg)
        min_col_index = 1  # 1-indexed
        max_col_index = self._csv_helper.columns_count + 1  # 1-indexed
        if min_col_index <= index <= max_col_index:
            return
        else:
            msg = f"Sequence index {index!r} must be greater than or equal to 1."
            raise exc.ValidationError(msg)

    def _normailse_header_or_index_to_index(
        self, header_attr: str, index_attr: str
    ) -> int:
        maybe_index: t.Optional[int] = self._get_arg(index_attr)
        if isinstance(maybe_index, int):
            index: int = maybe_index
        else:
            maybe_header: t.Optional[str] = self._get_arg(header_attr)
            index: int = self._normalise_header_to_index(maybe_header)
        return index

    def _normalise_header_to_index(self, maybe_header: t.Optional[str]) -> int:
        """
        Normalise the header to an index.

        Index is 1-indexed.
        """
        self._assert_has_validated_input()
        if maybe_header is None:
            raise exc.ValidationError("A valid header or index must be provided.")
        try:
            header_row = self._csv_helper.find_header_row(maybe_header)
            normal_index = self._csv_helper.find_header_index(maybe_header)
        except ValueError as e:
            raise exc.ValidationError(str(e))
        self._header_row_discovered = True
        self._header_row_index = header_row
        return normal_index

    def _normailse_skip_n_rows(self) -> int:
        skip_n_rows: int = self._get_arg(const.ARG_SKIP_N_ROWS)
        if self._header_row_discovered:
            # If the header has been discovered, then the first row after the
            # header is a data row, so we need to skip one extra row.
            #
            # I.e.:
            # - if the header is on row 0, then the first data row is on row 1, we skip 1 row
            # - if the header is on row 2, then the first data row is on row 3, we skip 3 rows

            skip_n_rows = self._header_row_index + 1
        return skip_n_rows

    def _normalise_output_to_file(self) -> Path:  # noqa: C901
        """
        Default to overwriting input file when no output path is specified. Also
        handles the case where the output path is a directory.
        """
        output_value: t.Optional[Path] = self._get_arg(const.ARG_OUTPUT)
        input_value: Path = self._get_arg(const.ARG_INPUT)
        # Default to overwriting input file when no output path is specified
        if output_value is None:
            normal_output_value = input_value
        elif output_value.exists() and output_value.is_file():
            normal_output_value = output_value
        elif output_value.exists() and output_value.is_dir():
            normal_output_value = output_value / input_value.name
        elif output_value.parent.exists() and not output_value.exists():
            normal_output_value = output_value
        else:
            msg = f"Output path {output_value!r} must exist or if it does not, its parent must exist."
            raise exc.ValidationError(msg)
        return normal_output_value

    def _check_write_permissions(self, path: Path) -> None:
        if not os.access(path, os.W_OK):
            raise exc.ValidationError(f"{path!r} is not writable.")

    def _check_read_permissions(self, path: Path) -> None:
        if not os.access(path, os.R_OK):
            raise exc.ValidationError(f"{path!r} is not readable.")


def get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transforms oligo sequences to a format that can be used in PyQuest"
    )
    # File arguments
    parser.add_argument(
        const.ARG_INPUT,
        type=Path,
        help=const.HELP__INPUT_FILE,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=const.HELP__OUTPUT_FILE,
        dest=const.ARG_OUTPUT,
    )

    return parser
