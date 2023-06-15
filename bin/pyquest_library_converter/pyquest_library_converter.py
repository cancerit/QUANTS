#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
import typing as t
import sys
import os
import argparse
import csv
from contextlib import contextmanager
from pathlib import Path
import tempfile
import shutil
from dataclasses import dataclass, field

if t.TYPE_CHECKING:
    import _csv

_TEMPLATE_GROUP_HEADER = "The column name or header in the CSV/TSV for the {}."
_TEMPLATE_GROUP_IDX = "1-indexed integer for the column index in a CSV/TSV for the {}."
_HELP__INPUT_FILE = "Input file path."
_HELP__OUTPUT_FILE = "By default, input file is overwritten with the output. You can specify a path to write to a specific file or a directory (appends input filename)."
_HELP__GROUP_SEQ = _TEMPLATE_GROUP_HEADER.format("oligo sequence itself")
_HELP__GROUP_SEQ_IDX = _TEMPLATE_GROUP_IDX.format("oligo sequence itself")
_HELP__GROUP_NAME = _TEMPLATE_GROUP_HEADER.format("oligo sequence name")
_HELP__GROUP_NAME_IDX = _TEMPLATE_GROUP_IDX.format("oligo sequence name")
_HELP__VERBOSE = "Print a summary."
_HELP__FORWARD_PRIMER = (
    "DNA primer to be removed from the start of the oligo sequence if provided."
)
_HELP__REVERSE_PRIMER = (
    "DNA primer to be removed from the end of the oligo sequence if provided."
)
_HELP_SKIP_N_ROWS = "Number of rows to skip in the CSV/TSV file before reading the data. By default, 1 row is skipped which assumes a header row. If you use the --name-header or --sequence-header options, you can set this to 0."

_ARG_INPUT = "input"
_ARG_OUTPUT = "output"
_ARG_VERBOSE = "verbose"
_ARG_FORWARD_PRIMER = "forward_primer"
_ARG_REVERSE_PRIMER = "reverse_primer"
_ARG_NAME_HEADER = "name_header"
_ARG_NAME_INDEX = "name_index"
_ARG_SEQ_HEADER = "sequence_header"
_ARG_SEQ_INDEX = "sequence_index"
_ARG_SKIP_N_ROWS = "skip_n_rows"

_OUTPUT_HEADER__ID = "#id"
_OUTPUT_HEADER__NAME = "name"
_OUTPUT_HEADER__SEQUENCE = "sequence"
_OUTPUT_DELIMETER = "\t"

if sys.version_info < (3, 8):
    raise RuntimeError("This script requires Python 3.8 or later")


class ValidationError(Exception):
    pass


@dataclass
class Report:
    row_count: int = 0
    forward_primers_trimmed: t.List[int] = field(default_factory=list, repr=False, hash=False)
    reverse_primers_trimmed: t.List[int] = field(default_factory=list, repr=False, hash=False)

    @property
    def both_trimmed(self) -> t.List[int]:
        both = list(set(self.forward_primers_trimmed) & set(self.reverse_primers_trimmed))
        both.sort()
        return both

    @property
    def forward_primers_trimmed_only(self) -> t.List[int]:
        forward_primers_only = list(set(self.forward_primers_trimmed) - set(self.reverse_primers_trimmed))
        forward_primers_only.sort()
        return forward_primers_only

    @property
    def reverse_primers_trimmed_only(self) -> t.List[int]:
        reverse_primers_only = list(set(self.reverse_primers_trimmed) - set(self.forward_primers_trimmed))
        reverse_primers_only.sort()
        return reverse_primers_only

    @staticmethod
    def compact_integer_sequence(seq: t.List[int]) -> str:
        """
        Compact a sorted series of unique integers into a more human-readable representation.

        Examples:
            >>> compact_integer_sequence([1, 2, 3, 4, 5, 8, 9, 10, 15, 20, 22, 23])
            '1-5, 8-10, 15, 20, 22-23'
        """
        if seq != sorted(set(seq)):
            raise ValueError("Input list must be sorted and contain unique values.")

        compacted = []
        start, end = seq[0], seq[0]
        for current in seq[1:]:
            # Continue the subsequence: if the current value directly proceeds
            # the last value by 1, then the subsequence continues.
            if current - end == 1:
                # Update the end of the subsequence for the next iteration.
                end = current

            # End the subsequence: if the current value does not directly proceed
            # the last value by 1, then the subsequence ends.
            else:
                # We write the last subsequence, if the subsequence is a single
                # value we write it as a digit but if the subsequence is more
                # than one value we write it as a range.
                as_range = f"{start}-{end}"
                as_digit = str(start)
                last_subsequence = as_digit if start == end else as_range
                compacted.append(last_subsequence)
                start = end = current

        # Handle the last element.
        as_range = f"{start}-{end}"
        as_digit = str(start)
        final_subsequence = as_digit if start == end else as_range
        compacted.append(final_subsequence)

        return ", ".join(compacted)

    def add_row(self, row_id: int, has_trimmed_forward_primer: bool, has_trimmed_reverse_primer: bool):
        self.row_count += 1
        if has_trimmed_forward_primer:
            self.forward_primers_trimmed.append(row_id)
        if has_trimmed_reverse_primer:
            self.reverse_primers_trimmed.append(row_id)
        return

    def summary(self) -> str:
        summary = []
        summary.append(f"Total rows selected: {self.row_count}")
        self.forward_primers_trimmed.sort()
        self.reverse_primers_trimmed.sort()
        both_detail = (
            self.compact_integer_sequence(self.both_trimmed)
            if self.both_trimmed
            else "None"
        )
        forward_primer_detail = (
            self.compact_integer_sequence(self.forward_primers_trimmed)
            if self.forward_primers_trimmed
            else "None"
        )
        reverse_primer = (
            self.compact_integer_sequence(self.reverse_primers_trimmed)
            if self.reverse_primers_trimmed
            else "None"
        )
        reverse_primer_only_detail = (
            self.compact_integer_sequence(self.reverse_primers_trimmed_only)
            if self.reverse_primers_trimmed_only
            else "None"
        )
        forward_primer_detail_only = (
            self.compact_integer_sequence(self.forward_primers_trimmed_only)
            if self.forward_primers_trimmed_only
            else "None"
        )
        summary.append(
            f"Rows with both forward and reverse trimmed ({len(self.both_trimmed)}): {both_detail}"
        )
        summary.append(
            f"Rows with forward trimmed ({len(self.forward_primers_trimmed)}): {forward_primer_detail}"
        )
        summary.append(
            f"Rows with forward trimmed only ({len(self.forward_primers_trimmed_only)}): {forward_primer_detail_only}"
        )
        summary.append(
            f"Rows with reverse trimmed ({len(self.reverse_primers_trimmed)}): {reverse_primer}"
        )
        summary.append(
            f"Rows with reverse trimmed only ({len(self.reverse_primers_trimmed_only)}): {reverse_primer_only_detail}"
        )
        return "\n".join(summary)


class CSVHelper:
    def __init__(
        self, file_path: Path, skip_n_rows: int, delimeter: t.Optional[str] = None
    ) -> None:
        self._file_path = file_path
        self._dialect = self._init_dialect() if delimeter is None else None
        self._delimeter = self._dialect.delimiter if delimeter is None else delimeter
        self._skip_n_rows = skip_n_rows
        self._start_row, self._start_offset = self._init_start_row_and_offset()
        self._columns_count = 0
        self._header_row_tup: t.Optional[t.Tuple[int, str]] = None

    def _init_dialect(self) -> csv.Dialect:
        """
        Get the dialect of a CSV or TSV file, while being able to handle large files and files with comments.
        """
        with open(self._file_path, newline="") as csvfile:
            chunk_size = 1024 * 1024  # 1MB
            sample = ""
            while len(sample) < chunk_size:
                line = csvfile.readline()
                # Stop if EOF is reached
                if not line:
                    break
                # Skip lines that start with '#'
                if line.startswith("#"):
                    continue
                sample += line
            dialect = csv.Sniffer().sniff(sample)
        return dialect

    def _init_start_row_and_offset(self) -> t.Tuple[int, int]:
        """
        Identify the byte-offset and 0-indexed start row in CSV file given that we need to skip the first n rows.
        """
        offset = 0
        result_offset = None

        current_row_idx = -1  # 0-indexed
        stop_row_idx = 0 + self._skip_n_rows  # 0-indexed

        line_count = 0
        with open(self._file_path, newline="") as csvfile:
            while True:
                line = csvfile.readline()
                offset = csvfile.tell() - len(line)
                current_row_idx += 1
                line_count += 1
                if stop_row_idx == current_row_idx:
                    result_idx = current_row_idx
                    result_offset = offset
                    break

        if result_offset is None:
            msg = (
                f"File {self._file_path!r} cannot calculate the offset, "
                f"because more rows were skipped ({self._skip_n_rows}) "
                "than there are in the file ({line_count})."
            )
            raise ValueError(msg)
        return result_idx, result_offset

    @contextmanager
    def get_csv_reader(self) -> t.Generator["_csv.reader", None, None]:
        """
        Get a CSV reader for the CSV file.

        This method returns a context manager that produces a CSV reader when
        entered. The delimiter used by the reader if it was provided to the
        constructor, else the dialect-delimiter and the rest of the dialect are
        used.

        When the context manager is exited, the CSV file is automatically
        closed.

        Yields:
            A context manager that produces a CSV reader when entered.

        Usage:
            >>> with csv_helper._get_csv_reader() as reader:
            ...     for row in reader:
            ...         print(row)
        """
        with open(self._file_path, newline="") as csvfile:
            csvfile.seek(self._start_offset)
            reader = (
                csv.reader(csvfile, delimiter=self._delimiter)
                if self._dialect is None
                else csv.reader(csvfile, dialect=self._dialect)
            )
            try:
                yield reader
            finally:
                pass

    def find_header_row(self, header: str) -> int:
        """
        Find the row number of a header in a CSV file, raising a ValueError if it is not found.

        Rows are 0-indexed, so the first row is row 0.
        """
        if self._header_row_tup is None or header not in self._header_row_tup:
            header_row = self._find_header_row(header)
            self._header_row_tup = (header_row, header)
        return self._header_row_tup[0]

    def _find_header_row(self, header: str) -> int:  # noqa: C901
        # We don't use the csv.reader here because we want to be able to handle
        # treating the file as a text file and not a CSV file, to make header
        # finding a substring-in-string problem.
        with open(self._file_path) as file:
            for i, line in enumerate(file):
                if i < self._skip_n_rows:
                    # Ignore the first n rows
                    continue
                elif header in line:
                    return i
                elif i > self._start_row:
                    msg = (
                        f"Header {header!r} not found in {self._file_path!r} after searching {i+1} rows. "
                        f"Perhaps it is not there or perhaps it was over-looked because you asked to skip {self._skip_n_rows} rows."
                    )
                    raise ValueError(msg)

    def find_header_index(self, header: str) -> int:
        """
        Find the index of a header in a CSV file, raising a ValueError if it is not found.

        Index is 1-indexed.
        """
        expected_row_idx = self.find_header_row(header)
        with self.get_csv_reader() as reader:
            for idx, row in enumerate(reader, start=self._skip_n_rows):
                if idx == expected_row_idx:
                    return row.index(header) + 1  # 1-indexed
        raise RuntimeError(
            f"Header {header!r} not found in row {row} but this should not happen."
        )

    @property
    def columns_count(self) -> int:
        """
        Get the number of columns in the CSV file.
        """
        if self._columns_count == 0:
            self._columns_count = self._get_columns_count()
        return self._columns_count

    def _get_columns_count(self) -> int:
        with self.get_csv_reader() as reader:
            for row in reader:
                return len(row)


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
        return self._get_arg(_ARG_INPUT)

    def get_clean_skip_n_rows(self) -> int:
        self._assert_has_validated_all()
        return self._normailse_skip_n_rows()

    def get_clean_output(self) -> Path:
        self._assert_has_validated_all()
        output: Path = self._normalise_output_to_file()
        return output

    def get_clean_forward_primer(self) -> str:
        self._assert_has_validated_all()
        return self._get_arg(_ARG_FORWARD_PRIMER)

    def get_clean_reverse_primer(self) -> str:
        self._assert_has_validated_all()
        return self._get_arg(_ARG_REVERSE_PRIMER)

    def get_clean_verbose(self) -> bool:
        self._assert_has_validated_all()
        return self._get_arg(_ARG_VERBOSE)

    def get_clean_name_index(self) -> int:
        self._assert_has_validated_all()
        index = self._normailse_header_or_index_to_index(
            header_attr=_ARG_NAME_HEADER,
            index_attr=_ARG_NAME_INDEX,
        )
        return index

    def get_clean_sequence_index(self) -> int:
        self._assert_has_validated_all()
        index = self._normailse_header_or_index_to_index(
            header_attr=_ARG_SEQ_HEADER,
            index_attr=_ARG_SEQ_INDEX,
        )
        return index

    def validate(self):
        validators = [
            self._validate_codependent_input_args,
            self._validate_output,
            self._validate_forward_primer,
            self._validate_reverse_primer,
            self._validate_name_index,
            self._validate_sequence_index,
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
        input_value: Path = self._get_arg(_ARG_INPUT)
        if not input_value.exists():
            raise ValidationError(f"Input file {input_value!r} does not exist.")
        if not input_value.is_file():
            raise ValidationError(f"Input file {input_value!r} is not a file.")
        self._check_read_permissions(input_value)
        return

    def __validate_skip_n_rows(self):
        skip_n_rows = self._get_arg(_ARG_SKIP_N_ROWS)
        if skip_n_rows < 0:
            msg = f"Skip n rows {skip_n_rows} must be >= 0."
            raise ValidationError(msg)
        return

    def _validate_output(self):
        output_file: Path = self._normalise_output_to_file()
        if output_file.parent.exists():
            self._check_write_permissions(output_file.parent)
        else:
            msg = f"Output file {output_file!r} directory does not exist."
            raise ValidationError(msg)
        return

    def _validate_sequence_index(self):
        index = self._normailse_header_or_index_to_index(
            header_attr=_ARG_SEQ_HEADER,
            index_attr=_ARG_SEQ_INDEX,
        )
        self._assert_valid_column_index(index)
        return

    def _validate_name_index(self):
        index = self._normailse_header_or_index_to_index(
            header_attr=_ARG_NAME_HEADER,
            index_attr=_ARG_NAME_INDEX,
        )
        self._assert_valid_column_index(index)
        return

    def _validate_forward_primer(self):
        forward_primer_value: str = self._get_arg(_ARG_FORWARD_PRIMER)
        allowed_chars = set(self._ALLOWED_DNA.upper())
        self._assert_valid_chars(forward_primer_value, allowed_chars)

    def _validate_reverse_primer(self):
        reverse_primer_value: str = self._get_arg(_ARG_REVERSE_PRIMER)
        allowed_chars = set(self._ALLOWED_DNA.upper())
        self._assert_valid_chars(reverse_primer_value, allowed_chars)

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
        file_path: Path = self._get_arg(_ARG_INPUT)
        skip_n_rows: int = self._get_arg(_ARG_SKIP_N_ROWS)
        try:
            self._csv_helper = CSVHelper(file_path, skip_n_rows)
        except ValueError as e:
            raise ValidationError(str(e))
        if self._csv_helper.columns_count < 2:
            msg = (
                f"Input file {file_path!r} has {self._csv_helper.columns_count} columns, "
                "but at least 2 are required."
            )
            raise ValidationError(msg)
        return

    def _assert_valid_chars(self, string: str, allowed_chars: t.Set[str]):
        for char in string:
            if char not in allowed_chars:
                msg = (
                    f"Character {char!r} in {string!r} is not in the allowed "
                    f"characters {allowed_chars!r} (case insensitive)."
                )
                raise ValidationError(msg)

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
            raise ValidationError(msg)

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
            raise ValidationError("A valid header or index must be provided.")
        try:
            header_row = self._csv_helper.find_header_row(maybe_header)
            normal_index = self._csv_helper.find_header_index(maybe_header)
        except ValueError as e:
            raise ValidationError(str(e))
        self._header_row_discovered = True
        self._header_row_index = header_row
        return normal_index

    def _normailse_skip_n_rows(self) -> int:
        skip_n_rows: int = self._get_arg(_ARG_SKIP_N_ROWS)
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
        output_value: t.Optional[Path] = self._get_arg(_ARG_OUTPUT)
        input_value: Path = self._get_arg(_ARG_INPUT)
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
            raise ValidationError(msg)
        return normal_output_value

    def _check_write_permissions(self, path: Path) -> None:
        if not os.access(path, os.W_OK):
            raise ValidationError(f"{path!r} is not writable.")

    def _check_read_permissions(self, path: Path) -> None:
        if not os.access(path, os.R_OK):
            raise ValidationError(f"{path!r} is not readable.")


def get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transforms oligo sequences to a format that can be used in PyQuest"
    )
    # File arguments
    parser.add_argument(_ARG_INPUT, type=Path, help=_HELP__INPUT_FILE)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=_HELP__OUTPUT_FILE,
        dest=_ARG_OUTPUT,
    )

    # Verbosity
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help=_HELP__VERBOSE,
        dest=_ARG_VERBOSE,
    )

    # DNA primer arguments (forward and reverse primers while we don't consider 5 and 3 prime ends or reverse complement complexity)
    parser.add_argument(
        "--forward",
        type=str,
        default="",
        help=_HELP__FORWARD_PRIMER,
        dest=_ARG_FORWARD_PRIMER,
    )
    parser.add_argument(
        "--reverse",
        type=str,
        default="",
        help=_HELP__REVERSE_PRIMER,
        dest=_ARG_REVERSE_PRIMER,
    )

    # Include a way to skip N rows of the input file
    parser.add_argument(
        "--skip",
        type=int,
        default=1,
        help=_HELP_SKIP_N_ROWS,
        dest=_ARG_SKIP_N_ROWS,
    )

    # Mutually exclusive argument group for oligo sequence name
    name_group = parser.add_mutually_exclusive_group(required=True)
    name_group.add_argument(
        "-n",
        "--name-header",
        type=str,
        help=_HELP__GROUP_NAME,
        dest=_ARG_NAME_HEADER,
    )
    name_group.add_argument(
        "-N",
        "--name-index",
        type=int,
        help=_HELP__GROUP_NAME_IDX,
        dest=_ARG_NAME_INDEX,
    )

    # Mutually exclusive argument group for oligo sequence
    sequence_group = parser.add_mutually_exclusive_group(required=True)
    sequence_group.add_argument(
        "-s",
        "--sequence-header",
        type=str,
        help=_HELP__GROUP_SEQ,
        dest=_ARG_SEQ_HEADER,
    )
    sequence_group.add_argument(
        "-S",
        "--sequence-index",
        type=int,
        help=_HELP__GROUP_SEQ_IDX,
        dest=_ARG_SEQ_INDEX,
    )
    return parser


###############################################################################
# Main and other main function related code
###############################################################################


def main(
    input_file: t.Union[str, Path],
    skip_n_rows: int,
    output_file: t.Union[str, Path],
    verbose: bool,
    forward_primer: str,
    reverse_primer: str,
    name_index: int,
    sequence_index: int,
):
    input_file = Path(input_file)
    output_file = Path(output_file)
    output_headers = [
        _OUTPUT_HEADER__ID,
        _OUTPUT_HEADER__NAME,
        _OUTPUT_HEADER__SEQUENCE,
    ]

    report = Report()
    # Prepare a temporary file to write to
    with tempfile.NamedTemporaryFile(delete=True) as temp_handle:
        temp_file = Path(temp_handle.name)

        # Read the input file and write to a temporary file
        csv_helper = CSVHelper(input_file, skip_n_rows=skip_n_rows)
        with csv_helper.get_csv_reader() as csv_reader:
            dict_rows = filter_rows(
                csv_reader, name_index=name_index, sequence_index=sequence_index
            )
            dict_rows = trim_sequences(
                dict_rows, forward_primer=forward_primer, reverse_primer=reverse_primer, report=report
            )
            write_rows(dict_rows, output_file=temp_file, headers=output_headers)

        # Copy the temporary file to the output file
        shutil.copy(temp_file, output_file)

    # At this point, the temporary file has been deleted
    if verbose:
        print(report.summary())
    return


def filter_rows(
    rows: t.Iterator[t.List[str]],
    name_index: int,
    sequence_index: int,
    index_offset: int = 0,
) -> t.Iterable[t.Dict[str, str]]:
    """
    Filter rows to only include the name and sequence columns, giving rows a new 1-based index.

    Name and sequence columns are specified by their 1-based index in the input file.

    Yield dictionaries of index, name, sequence values from each row, where keys are the new headers.
    """
    name_index_0 = name_index - 1
    sequence_index_0 = sequence_index - 1
    index_start_1 = 1 + index_offset
    for idx_1, row in enumerate(rows, start=index_start_1):
        name = row[name_index_0]
        sequence = row[sequence_index_0]
        dict_row = {
            _OUTPUT_HEADER__ID: idx_1,
            _OUTPUT_HEADER__NAME: name,
            _OUTPUT_HEADER__SEQUENCE: sequence,
        }
        yield dict_row


def trim_sequences(
    dict_rows: t.Iterator[t.Dict[str, str]], forward_primer: str, reverse_primer: str, report: Report
) -> t.Iterable[t.Dict[str, str]]:
    """
    Trim the forward and reverse primer from the sequence.

    Yield dictionaries of index, name, sequence values from each row, where keys are the new headers.
    """
    for dict_row in dict_rows:
        # Trim the sequence and update the dictionary
        sequence = dict_row[_OUTPUT_HEADER__SEQUENCE]
        trimmed_sequence, has_trimmed_forward_primer, has_trimmed_reverse_primer = trim_sequence(
            sequence, forward_primer, reverse_primer
        )
        dict_row[_OUTPUT_HEADER__SEQUENCE] = trimmed_sequence

        # Update the report
        row_id = dict_row[_OUTPUT_HEADER__ID]
        report.add_row(row_id, has_trimmed_forward_primer, has_trimmed_reverse_primer)
        yield dict_row


def trim_sequence(sequence: str, forward_primer: str, reverse_primer: str) -> t.Tuple[str, bool, bool]:
    """
    Trim the forward and reverse primer from the sequence.

    Return the trimmed sequence and whether the forward and reverse primer were trimmed.
    """
    start_index: int = 0
    # None is the end of the string, and works for slicing
    end_index: t.Optional[int] = None
    has_trimmed_forward_primer = False
    has_trimmed_reverse_primer = False

    err_msg = f"The forward and reverse primer overlap in the sequence (no handling in code yet): {forward_primer=}, {reverse_primer=}, {sequence=}"

    forward_primer_exists = len(forward_primer) and sequence.startswith(forward_primer)
    reverse_primer_exists = len(reverse_primer) and sequence.endswith(reverse_primer)

    is_overlapping = False

    if forward_primer_exists:
        temp_index = len(forward_primer)
        reverse_primer_exists_after_trimming = sequence[temp_index:].endswith(reverse_primer)
        is_overlapping = reverse_primer_exists and not reverse_primer_exists_after_trimming
        start_index = temp_index
        has_trimmed_forward_primer = True

    if reverse_primer_exists:
        temp_index = len(sequence) - len(reverse_primer)
        forward_primer_exists_after_trimming = sequence[:temp_index].startswith(forward_primer)
        is_overlapping = forward_primer_exists and not forward_primer_exists_after_trimming
        end_index = temp_index
        has_trimmed_reverse_primer = True

    if is_overlapping:
        raise NotImplementedError(err_msg)

    trimmed_sequence = sequence[start_index:end_index]

    return (trimmed_sequence, has_trimmed_forward_primer, has_trimmed_reverse_primer)


def write_rows(
    dict_rows: t.Iterator[t.Dict[str, str]], headers: t.List[str], output_file: Path
) -> None:
    """
    Write rows to output file.
    """
    with open(output_file, "w") as output:
        csv_writer = csv.DictWriter(
            output, fieldnames=headers, delimiter=_OUTPUT_DELIMETER
        )
        csv_writer.writeheader()
        csv_writer.writerows(dict_rows)


if __name__ == "__main__":
    parser = get_argparser()
    namespace = parser.parse_args()
    cleaner = ArgsCleaner(namespace)
    try:
        cleaner.validate()
    except ValidationError as err:
        error_detail = str(err)
        error_msg = f"Error: Argument validation!\n{error_detail}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    main(
        input_file=cleaner.get_clean_input(),
        skip_n_rows=cleaner.get_clean_skip_n_rows(),
        output_file=cleaner.get_clean_output(),
        verbose=cleaner.get_clean_verbose(),
        forward_primer=cleaner.get_clean_forward_primer(),
        reverse_primer=cleaner.get_clean_reverse_primer(),
        name_index=cleaner.get_clean_name_index(),
        sequence_index=cleaner.get_clean_sequence_index(),
    )
