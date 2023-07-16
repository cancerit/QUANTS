import typing as t
import os
from pathlib import Path
from textwrap import dedent
from pprint import pformat
from types import MappingProxyType

from src.exceptions import ValidationError
from src import constants as const
from src.dna.helpers import find_invalid_chars_in_dna_sequence
from src.csv.csv_helper import CSVHelper
from src.enums import NameAndSequenceArgs
from src.cli import display_warning

if t.TYPE_CHECKING:
    import argparse


class ArgsCleaner:
    def __init__(self, namespace: "argparse.Namespace"):
        # Read-only to prevent accidental modification
        self._namespace_dict = MappingProxyType(vars(namespace).copy())
        self._parsed_csv = None
        self._validated = False
        self._validated_input = False
        self._scanned_for_headers = False
        self._csv_helper: "t.Optional[CSVHelper]" = None
        self._header_row_discovered = False
        self._use_forced_header_index = False
        self._header_row_index_0_idx = -1
        self._computed_skip_n_rows = None

    def summary(self) -> str:
        """
        Return a summary of namespace arguments and clean arguments.
        """
        raw_input = self._get_arg(const._ARG_INPUT)
        raw_output = self._get_arg(const._ARG_OUTPUT)
        raw_verbose = self._get_arg(const._ARG_VERBOSE)
        raw_skip_n_rows = self._get_arg(const._ARG_SKIP_N_ROWS)
        raw_forward_primer = self._get_arg(const._ARG_FORWARD_PRIMER)
        raw_reverse_primer = self._get_arg(const._ARG_REVERSE_PRIMER)
        raw_name_header = self._get_arg(const._ARG_NAME_HEADER)
        raw_name_index = self._get_arg(const._ARG_NAME_INDEX)
        raw_sequence_header = self._get_arg(const._ARG_SEQ_HEADER)
        raw_sequence_index = self._get_arg(const._ARG_SEQ_INDEX)
        raw_reverse_complement_flag = self._get_arg(const._ARG_REVERSE_COMPLEMENT_FLAG)
        raw_force_header_index = self._get_arg(const._ARG_FORCE_HEADER_INDEX)
        is_validated = self._validated
        if is_validated:
            clean_input = self.get_clean_input()
            clean_output = self.get_clean_output()
            clean_verbose = self.get_clean_verbose()
            clean_forced_header_index = self.get_clean_forced_header_index()
            clean_skip_n_rows = self.get_clean_adjusted_skip_n_rows()
            is_forced = " (forced)" if clean_forced_header_index is not None else ""
            clean_forward_primer = self.get_clean_forward_primer()
            clean_reverse_primer = self.get_clean_reverse_primer()
            clean_name_index = self.get_clean_name_index()
            clean_sequence_index = self.get_clean_sequence_index()
            clean_reverse_complement_flag = self.get_clean_reverse_complement_flag()
        else:
            special_value = "N/A"
            clean_input = special_value
            clean_output = special_value
            clean_verbose = special_value
            clean_skip_n_rows = special_value
            clean_forced_header_index = special_value
            is_forced = ""
            clean_forward_primer = special_value
            clean_reverse_primer = special_value
            clean_name_index = special_value
            clean_sequence_index = special_value
            clean_reverse_complement_flag = special_value
        summary = f"""\
        Is Validated: {is_validated}
        Input: {str(raw_input)!r} -> {str(clean_input)!r}
        Output: {str(raw_output)!r} -> {str(clean_output)!r}
        Verbose: {raw_verbose!r} -> {clean_verbose!r}
        Skip N Rows: {raw_skip_n_rows!r} -> {clean_skip_n_rows!r}{is_forced}
        Forward Primer: {raw_forward_primer!r} -> {clean_forward_primer!r}
        Reverse Primer: {raw_reverse_primer!r} -> {clean_reverse_primer!r}
        Name Header: {raw_name_header!r} -> {clean_name_index!r}
        Name Index: {raw_name_index!r} -> {clean_name_index!r}
        Sequence Header: {raw_sequence_header!r} -> {clean_sequence_index!r}
        Sequence Index: {raw_sequence_index!r} -> {raw_sequence_index!r}
        Reverse Complement Flag: {raw_reverse_complement_flag!r} -> {clean_reverse_complement_flag!r}
        Force Header Index: {raw_force_header_index!r} -> {clean_forced_header_index!r}
        """
        summary = dedent(summary).rstrip()
        return summary

    def _get_arg(self, arg_name: str) -> t.Any:
        if arg_name not in self._namespace_dict:
            namespace = pformat(self._namespace_dict)
            msg = (
                f"Argument {arg_name!r} no longer has an attribute on the "
                "namespace object, which suggests "
                f"the arg parser has changed:\n{namespace}"
            )
            raise AttributeError(msg)
        return self._namespace_dict[arg_name]

    def to_clean_dict(self) -> t.Dict[str, t.Any]:
        KEY_INPUT = const._ARG_INPUT
        KEY_OUTPUT = const._ARG_OUTPUT
        KEY_VERBOSE = const._ARG_VERBOSE
        KEY_ADJUSTED_SKIP_N_ROWS = const.KEY_ADJUSTED_SKIP_N_ROWS
        KEY_FORWARD_PRIMER = const._ARG_FORWARD_PRIMER
        KEY_REVERSE_PRIMER = const._ARG_REVERSE_PRIMER
        KEY_NAME_INDEX = const._ARG_NAME_INDEX
        KEY_SEQUENCE_INDEX = const._ARG_SEQ_INDEX
        KEY_REVERSE_COMPLEMENT_FLAG = const._ARG_REVERSE_COMPLEMENT_FLAG
        KEY_FORCE_HEADER_INDEX = const._ARG_FORCE_HEADER_INDEX
        clean_dict = {
            KEY_INPUT: self.get_clean_input(),
            KEY_ADJUSTED_SKIP_N_ROWS: self.get_clean_adjusted_skip_n_rows(),
            KEY_OUTPUT: self.get_clean_output(),
            KEY_VERBOSE: self.get_clean_verbose(),
            KEY_FORWARD_PRIMER: self.get_clean_forward_primer(),
            KEY_REVERSE_PRIMER: self.get_clean_reverse_primer(),
            KEY_NAME_INDEX: self.get_clean_name_index(),
            KEY_SEQUENCE_INDEX: self.get_clean_sequence_index(),
            KEY_REVERSE_COMPLEMENT_FLAG: self.get_clean_reverse_complement_flag(),
            KEY_FORCE_HEADER_INDEX: self.get_clean_forced_header_index(),
        }
        return clean_dict

    def get_clean_input(self) -> Path:
        self._assert_has_validated_all()
        return self._get_arg(const._ARG_INPUT)

    def get_clean_adjusted_skip_n_rows(self) -> int:
        self._assert_has_validated_all()
        adjusted = self._computed_skip_n_rows
        if adjusted is None:
            raise RuntimeError("Skip N Rows has not been computed yet")
        return adjusted

    def get_clean_forced_header_index(self) -> t.Optional[int]:
        self._assert_has_validated_all()
        return self._get_arg(const._ARG_FORCE_HEADER_INDEX)

    def get_clean_output(self) -> Path:
        self._assert_has_validated_all()
        output: Path = self._normalise_output_to_file()
        return output

    def get_clean_forward_primer(self) -> str:
        self._assert_has_validated_all()
        return self._get_arg(const._ARG_FORWARD_PRIMER)

    def get_clean_reverse_primer(self) -> str:
        self._assert_has_validated_all()
        return self._get_arg(const._ARG_REVERSE_PRIMER)

    def get_clean_verbose(self) -> bool:
        self._assert_has_validated_all()
        return self._get_arg(const._ARG_VERBOSE)

    def get_clean_name_index(self) -> int:
        self._assert_has_validated_all()
        index = self._normalise_header_or_index_to_index(
            header_attr=const._ARG_NAME_HEADER,
            index_attr=const._ARG_NAME_INDEX,
        )
        return index

    def get_clean_sequence_index(self) -> int:
        self._assert_has_validated_all()
        index = self._normalise_header_or_index_to_index(
            header_attr=const._ARG_SEQ_HEADER,
            index_attr=const._ARG_SEQ_INDEX,
        )
        return index

    def get_clean_reverse_complement_flag(self) -> bool:
        self._assert_has_validated_all()
        return self._get_arg(const._ARG_REVERSE_COMPLEMENT_FLAG)

    def validate(self):
        validators = [
            self._validate_codependent_input_args,
            self._validate_output,
            self._validate_forward_primer,
            self._validate_reverse_primer,
            self._validate_reverse_complement_flag,
        ]
        for validator in validators:
            validator()
        self._validated = True
        return

    def _validate_codependent_input_args(self):
        self.__validate_input()
        self._assert_or_set_csv_helper()
        self._validate_force_header_index()
        self._validate_name_arg_and_sequence_arg_types_together()
        self._validate_name_index_and_sequence_index_values_together()
        self._validate_name_index()
        self._validate_sequence_index()
        self._scan_for_header_row()
        self.__validate_skip_n_rows()
        return

    def __validate_input(self):
        input_value: Path = self._get_arg(const._ARG_INPUT)
        if not input_value.exists():
            raise ValidationError(f"Input file {str(input_value)!r} does not exist.")
        if not input_value.is_file():
            raise ValidationError(f"Input file {str(input_value)!r} is not a file.")
        self._check_read_permissions(input_value)
        self._validated_input = True
        return

    def __validate_skip_n_rows(self):
        skip_n_rows = self._get_arg(const._ARG_SKIP_N_ROWS)
        if skip_n_rows < 0:
            msg = f"Skip n rows {skip_n_rows} must be >= 0."
            raise ValidationError(msg)
        self._computed_skip_n_rows = self._normailse_skip_n_rows()
        return

    def _validate_output(self):
        output_file: Path = self._normalise_output_to_file()
        if output_file.parent.exists():
            self._check_write_permissions(output_file.parent)
        else:
            msg = f"Output file {str(output_file)!r} directory does not exist."
            raise ValidationError(msg)
        input_file = self._get_arg(const._ARG_INPUT)
        if input_file == output_file:
            msg = (
                f"Input file {str(input_file)!r} and output file {str(output_file)!r} must "
                "not be the same."
            )
            raise ValidationError(msg)
        return

    def _validate_sequence_index(self):
        index = self._normalise_header_or_index_to_index(
            header_attr=const._ARG_SEQ_HEADER,
            index_attr=const._ARG_SEQ_INDEX,
        )
        self._assert_valid_column_index(index, "sequence")
        return

    def _validate_name_index(self):
        index = self._normalise_header_or_index_to_index(
            header_attr=const._ARG_NAME_HEADER,
            index_attr=const._ARG_NAME_INDEX,
        )
        self._assert_valid_column_index(index, "name")
        return

    def _validate_name_index_and_sequence_index_values_together(self):
        name_index = self._normalise_header_or_index_to_index(
            header_attr=const._ARG_NAME_HEADER,
            index_attr=const._ARG_NAME_INDEX,
        )
        sequence_index = self._normalise_header_or_index_to_index(
            header_attr=const._ARG_SEQ_HEADER,
            index_attr=const._ARG_SEQ_INDEX,
        )
        if name_index == sequence_index:
            msg = "Name column and sequence column must not be the same."
            raise ValidationError(msg)
        return

    def _validate_name_arg_and_sequence_arg_types_together(self):
        arg_type = self._get_argument_type_used_by_name_and_sequence()

        if arg_type == NameAndSequenceArgs.MIXED:
            name_index = self._get_arg(const._ARG_NAME_INDEX)
            sequence_index = self._get_arg(const._ARG_SEQ_INDEX)
            name_header = self._get_arg(const._ARG_NAME_HEADER)
            sequence_header = self._get_arg(const._ARG_SEQ_HEADER)
            name_i = str(name_index) if name_index is not None else ""
            seq_i = str(sequence_index) if sequence_index is not None else ""
            name_h = str(name_header) if name_header is not None else ""
            seq_i = str(sequence_header) if sequence_header is not None else ""
            detail = f"Index: {name_i!r} & {seq_i!r}. Header: {name_h!r} & {seq_i!r}"
            msg = f"Cannot use a mix of indices and headers for name and sequence columns. {detail}"
            raise ValidationError(msg)
        elif arg_type == NameAndSequenceArgs.NONE:
            msg = "Must specify both name and sequence columns."
            raise ValidationError(msg)
        return

    def _validate_forward_primer(self):
        forward_primer_value: str = self._get_arg(const._ARG_FORWARD_PRIMER)
        self._assert_valid_primer(forward_primer_value, "forward primer")

    def _validate_reverse_primer(self):
        reverse_primer_value: str = self._get_arg(const._ARG_REVERSE_PRIMER)
        self._assert_valid_primer(reverse_primer_value, "reverse primer")

    def _validate_reverse_complement_flag(self):
        flag = self._get_arg(const._ARG_REVERSE_COMPLEMENT_FLAG)
        if not isinstance(flag, bool):
            msg = f"Reverse complement flag {flag!r} must be a boolean."
            raise ValidationError(msg)
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
            msg = "The index cannot be validated before input file has been validated."
            raise RuntimeError(msg)

    def _assert_has_validated_force_header_index(self):
        if not self._use_forced_header_index:
            msg = "The skip_n_row cannot be validated before forced header index has been validated."
            raise RuntimeError(msg)

    def _assert_has_scanned_for_headers(self):
        if not self._scanned_for_headers:
            msg = "The index cannot be validated before input file has been scanned for headers."
            raise RuntimeError(msg)
        return

    def _assert_or_set_csv_helper(self):
        file_path: Path = self._get_arg(const._ARG_INPUT)
        try:
            self._csv_helper = CSVHelper(file_path)
        except ValueError as e:
            raise ValidationError(str(e))
        if self._csv_helper.columns_count < 2:
            msg = (
                f"Input file {file_path!r} has {self._csv_helper.columns_count} columns, "
                "but at least 2 are required."
            )
            raise ValidationError(msg)
        return

    def _assert_valid_primer(self, primer: str, primer_type: str):
        if not primer:
            # Empty primer is allowed
            return
        illegal_chars, allowed_chars = find_invalid_chars_in_dna_sequence(
            primer, allow_n=False, allow_lower_case=False
        )
        if illegal_chars:
            illegal_str = "".join(illegal_chars)
            allowed_str = "".join(allowed_chars)
            msg = (
                f"Illegal characters {illegal_str!r} found in {primer_type}. "
                "Only the following characters are exactly allowed: "
                f"{allowed_str!r} (case sensitive)."
            )
            raise ValidationError(msg)

    def _assert_valid_column_index(self, index: int, name: str):
        """
        Index is 1-indexed.
        """
        self._assert_has_validated_input()
        if not self._validated_input:
            msg = "The index cannot be validated before input file has been validated."
            raise RuntimeError(msg)
        min_col_index = 1  # 1-indexed
        max_col_index = self._csv_helper.columns_count  # 1-indexed
        if min_col_index <= index <= max_col_index:
            return
        else:
            msg = f"{name.capitalize()} index is out of range, got {index!r}. Expected {min_col_index!r} <= index <= {max_col_index!r}."
            raise ValidationError(msg)

    def _normalise_header_or_index_to_index(
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
            raise ValidationError("A valid header or index must be provided.")
        column_index_1_idx = self._csv_helper.find_column_index_by_header(
            maybe_header,
            one_index=True,
        )
        if column_index_1_idx == -1:
            msg = f"Header {maybe_header!r} not found in input file ."
            raise ValidationError(msg)

        return column_index_1_idx

    def _normailse_skip_n_rows(self) -> int:
        self._assert_has_validated_input()
        self._assert_has_scanned_for_headers()
        self._assert_has_validated_force_header_index()
        # The user states they want to skip N rows
        # We must first calutate the implicit offset ie. the number of rows to automatically skip before the user specified N rows are skipped:
        # - we do this to consider the case where the file may have file headers (aka file comments)
        # - we do this to consider the case where the file may have a header row
        # We must then calculate the explicit offset ie. the number of rows to skip after the implicit offset

        # Prepare implicit offset variables
        has_detected_header_row = self._header_row_index_0_idx != -1
        force_header_index_1_idx = self._get_arg(const._ARG_FORCE_HEADER_INDEX)
        force_header_index_0_idx = (
            force_header_index_1_idx - 1
            if force_header_index_1_idx is not None
            else None
        )
        has_forced_header_index = self._use_forced_header_index

        # Find the implicit offset
        if has_forced_header_index and force_header_index_0_idx is not None:
            # The forced header index takes precedence over other methods
            #
            # We add 1 to the header row index to account for the header row itself
            # as the user is uninterested in the header row
            implicit_offset = force_header_index_0_idx + 1
        elif has_detected_header_row:
            # We add 1 to the header row index to account for the header row itself
            # as the user is uninterested in the header row
            implicit_offset = self._header_row_index_0_idx + 1
        else:
            # Otherwise, we assume the file has no header row and so the
            # implicit offset is 0 + any file headers/file comments detected
            (
                first_tabular_row_0_idx,
                _,
            ) = self._csv_helper._find_first_tabular_row_idx_and_offset(one_index=False)
            implicit_offset = first_tabular_row_0_idx

        # Find the explicit offset
        skip_n_rows: int = self._get_arg(const._ARG_SKIP_N_ROWS)
        explicit_offset = skip_n_rows

        # Compute the accuracte "skip_n_rows" value
        result = implicit_offset + explicit_offset

        # Finally check the result is not out of bounds
        line_count = self._csv_helper.line_count
        data_row_count = line_count - implicit_offset
        if result > data_row_count:
            detail = f" ({line_count} if including file headers/file comments)"
            msg = f"Skip N rows value {result!r} is greater than the number of data in the file: {data_row_count}{detail}."
            raise ValidationError(msg)
        return result

    def _validate_force_header_index(self) -> t.Optional[int]:
        index: t.Optional[int] = self._get_arg(const._ARG_FORCE_HEADER_INDEX)
        if index is None:
            self._use_forced_header_index = True
            return None
        else:
            line_count = self._csv_helper.line_count
            if index < 1:
                msg = f"Header index {index!r} must be greater than or equal to 1."
                raise ValidationError(msg)
            elif index > line_count:
                msg = (
                    f"Header index {index!r} must be less than or equal to the number of lines in the file: "
                    f"{line_count}."
                )
                raise ValidationError(msg)
            self._use_forced_header_index = True
            return index

    def _normalise_output_to_file(self) -> Path:  # noqa: C901
        """
        Default to overwriting input file when no output path is specified. Also
        handles the case where the output path is a directory.
        """
        output_value: t.Optional[Path] = self._get_arg(const._ARG_OUTPUT)
        input_value: Path = self._get_arg(const._ARG_INPUT)
        # Default to overwriting input file when no output path is specified
        if output_value is None:
            raise ValidationError("Output path must be specified.")
        elif output_value.exists() and output_value.is_file():
            normal_output_value = output_value
        elif output_value.exists() and output_value.is_dir():
            normal_output_value = (
                output_value / f"{input_value.stem}.out{input_value.suffix}"
            )
        elif output_value.parent.exists() and not output_value.exists():
            normal_output_value = output_value
        else:
            msg = f"Output path {output_value!r} must exist or if it does not, its parent must exist."
            raise ValidationError(msg)
        return normal_output_value

    def _check_write_permissions(self, path: Path) -> None:
        if not os.access(path, os.W_OK):
            raise ValidationError(f"{path!r} is not writable.")

    def _check_read_permissions(self, path: Path) -> None:
        if not os.access(path, os.R_OK):
            raise ValidationError(f"{path!r} is not readable.")

    def _get_argument_type_used_by_name_and_sequence(self) -> NameAndSequenceArgs:
        name_index = self._get_arg(const._ARG_NAME_INDEX)
        sequence_index = self._get_arg(const._ARG_SEQ_INDEX)
        name_header = self._get_arg(const._ARG_NAME_HEADER)
        sequence_header = self._get_arg(const._ARG_SEQ_HEADER)
        # Users can either specify a pair of indexes or a pair of headers. A mix
        # of the two is not allowed.
        uses_headers = name_header is not None or sequence_header is not None
        uses_indexes = name_index is not None or sequence_index is not None
        if uses_headers and uses_indexes:
            result = NameAndSequenceArgs.MIXED
        elif uses_headers:
            result = NameAndSequenceArgs.HEADER
        elif uses_indexes:
            result = NameAndSequenceArgs.INDEX
        else:
            result = NameAndSequenceArgs.NONE
        return result

    def _scan_for_header_row(self):
        self._assert_has_validated_input()
        arg_type = self._get_argument_type_used_by_name_and_sequence()
        line_count = self._csv_helper.line_count
        is_unreliable_heuristic = line_count < 5
        if is_unreliable_heuristic and arg_type == NameAndSequenceArgs.INDEX:
            header_index = -1
            display_warning(const.WARN_HEADER_SCAN_ABORTED)
        elif arg_type == NameAndSequenceArgs.INDEX:
            header_index = self._csv_helper.find_header_row_index(
                one_index=False,
            )
        elif arg_type == NameAndSequenceArgs.HEADER:
            name_header = self._get_arg(const._ARG_NAME_HEADER)
            sequence_header = self._get_arg(const._ARG_SEQ_HEADER)
            header_index = self._csv_helper.find_header_row_index_by_header(
                name_header,
                sequence_header,
                one_index=False,
            )
        else:
            raise RuntimeError(
                "Cannot scan for headers, but this error is unreachable if validate was called first."
            )
        self._scanned_for_headers = True
        self._header_row_index_0_idx = header_index
        return
