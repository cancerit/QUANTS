#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import typing as t
import sys
import os
import argparse
import csv
from contextlib import contextmanager
from functools import partial
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
_HELP__SKIP_N_ROWS = "Number of rows to skip in the CSV/TSV file before reading the data. By default, 1 row is skipped which assumes a header row. If you use the --name-header or --sequence-header options, you can set this to 0."
_HELP__REVERSE_COMPLEMENT_FLAG = "Reverse complement the oligo sequence."

_ARG_INPUT = "input"
_ARG_OUTPUT = "output"
_ARG_VERBOSE = "verbose"
_ARG_FORWARD_PRIMER = "forward_primer"
_ARG_REVERSE_PRIMER = "reverse_primer"
_ARG_REVERSE_COMPLEMENT_FLAG = "reverse_complement_flag"
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


class UndevelopedFeatureError(Exception):
    pass


@dataclass
class Report:
    row_count: int = 0
    forward_primers_trimmed: t.List[int] = field(
        default_factory=list, repr=False, hash=False
    )
    reverse_primers_trimmed: t.List[int] = field(
        default_factory=list, repr=False, hash=False
    )
    scanning_summary: t.List[str] = field(
        default_factory=list, repr=False, hash=False, init=True
    )

    @property
    def both_trimmed(self) -> t.List[int]:
        both = list(
            set(self.forward_primers_trimmed) & set(self.reverse_primers_trimmed)
        )
        both.sort()
        return both

    def add_row(
        self,
        row_id: int,
        has_trimmed_forward_primer: bool,
        has_trimmed_reverse_primer: bool,
    ):
        self.row_count += 1
        if has_trimmed_forward_primer:
            self.forward_primers_trimmed.append(row_id)
        if has_trimmed_reverse_primer:
            self.reverse_primers_trimmed.append(row_id)
        return

    def add_scanning_summary(self, scanning_summary: t.List[str]):
        self.scanning_summary = scanning_summary
        return

    def summary(self) -> str:
        summary = self.scanning_summary.copy()
        total = self.row_count
        self.forward_primers_trimmed.sort()
        self.reverse_primers_trimmed.sort()
        summary.append(
            f"Forward primer trimmed in {len(self.forward_primers_trimmed)} of {total} sequences."
        )
        summary.append(
            f"Reverse primer trimmed in {len(self.reverse_primers_trimmed)} of {total} sequences."
        )
        summary.append(
            f"Forward + reverse primer trimmed in {len(self.both_trimmed)} out of {total} sequences."
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


class PrimerScanner:
    """
    PrimmerScanner is a class that scans a CSV file, using the given forward and
    reverse primers and identifies whether to use the orginal or reverse
    complement of each primer for downstream usage, e.g. trimming.
    """

    def __init__(self, forward_primer: str, reverse_primer: str) -> None:
        self._given_forward_primer = forward_primer
        self._given_reverse_primer = reverse_primer
        self._given_forward_primer_revcomp = reverse_complement(forward_primer)
        self._given_reverse_primer_revcomp = reverse_complement(reverse_primer)
        self.__init_counters()
        self._has_scanned = False

    def __init_counter_dict(self, original: str, revcomp: str) -> t.Dict[str, int]:
        return {original: 0, revcomp: 0}

    def __init_counters(self) -> t.Tuple[t.Dict[str, int], t.Dict[str, int]]:
        self._forward_primer_counter: t.Dict[str, int] = self.__init_counter_dict(
            self._given_forward_primer, self._given_forward_primer_revcomp
        )
        self._reverse_primer_counter: t.Dict[str, int] = self.__init_counter_dict(
            self._given_reverse_primer, self._given_reverse_primer_revcomp
        )
        self._total_oligos_scanned = 0

    def summary(self) -> t.List[str]:
        """
        Get a summary of the scanning results.
        """
        self._assert_has_scanned()
        total = self._total_oligos_scanned
        forward_cnt = self._forward_primer_counter[self._given_forward_primer]
        forward_revcomp_cnt = self._forward_primer_counter[
            self._given_forward_primer_revcomp
        ]
        reverse_cnt = self._reverse_primer_counter[self._given_reverse_primer]
        reverse_revcomp_cnt = self._reverse_primer_counter[
            self._given_reverse_primer_revcomp
        ]
        predicted_fwd_primer = self.predict_forward_primer()
        predicted_rev_primer = self.predict_reverse_primer()
        # If a user speficies a forward primer as an empty string, then we we do not need to document the search for it
        natural_empty_fwd_primer = (
            predicted_fwd_primer == ""
            and predicted_fwd_primer == self._given_forward_primer_revcomp
        )
        natural_empty_rev_primer = (
            predicted_rev_primer == ""
            and predicted_rev_primer == self._given_reverse_primer_revcomp
        )
        search_fwd_lines = [
            f"Forward primer found {forward_cnt} times in {total} sequences scanned.",
            f"Forward primer reverse complement found {forward_revcomp_cnt} times in {total} sequences scanned.",
        ]
        search_rev_lines = [
            f"Reverse primer found {reverse_cnt} times in {total} sequences scanned",
            f"Reverse primer reverse complement found {reverse_revcomp_cnt} times in {total} sequences scanned.",
        ]
        search_fwd_lines = (
            ["Forward primer search was unnecessary because it is an empty string."]
            if natural_empty_fwd_primer
            else search_fwd_lines
        )
        search_rev_lines = (
            ["Reverse primer search was unnecessary because it is an empty string."]
            if natural_empty_rev_primer
            else search_rev_lines
        )

        chosen_fwd_line = self._summary_chosen_primer(
            predicted_primer=predicted_fwd_primer,
            primer_name="forward",
            given_original_primer=self._given_forward_primer,
            given_revcomp_primer=self._given_forward_primer_revcomp,
            original_count=forward_cnt,
            revcomp_count=forward_revcomp_cnt,
        )

        chosen_rev_line = self._summary_chosen_primer(
            predicted_primer=predicted_rev_primer,
            primer_name="reverse",
            given_original_primer=self._given_reverse_primer,
            given_revcomp_primer=self._given_reverse_primer_revcomp,
            original_count=reverse_cnt,
            revcomp_count=reverse_revcomp_cnt,
        )
        lines = (
            [f"Total seqeunces processed: {total}"]
            + search_fwd_lines
            + search_rev_lines
            + [chosen_fwd_line, chosen_rev_line]
        )
        return lines

    def _summary_chosen_primer(
        self,
        predicted_primer: str,
        given_original_primer: str,
        given_revcomp_primer: str,
        primer_name: str,
        original_count: int,
        revcomp_count: str,
    ) -> str:
        if not predicted_primer and original_count == 0 and revcomp_count == 0:
            chosen_line = f"WARNING: Chosen {primer_name} primer is an empty string because the forward primer was not found in any of the sequences"
        elif not predicted_primer and not given_original_primer:
            chosen_line = f"Chosen {primer_name} primer is an empty string"
        elif predicted_primer == given_original_primer:
            chosen_line = f"Chosen {primer_name} primer is the same as the given {primer_name} primer"
        elif predicted_primer == given_revcomp_primer:
            chosen_line = f"Chosen {primer_name} primer is the reverse complement of the given {primer_name} primer"
        else:
            raise NotImplementedError("Unhandled case - please report this as a bug")
        return chosen_line + f": {predicted_primer!r}."

    def scan_all(self, oligos: t.List[str]) -> None:
        """
        Scan all oligos and count the number of times the given forward and reverse primers or their respective reverse complements are found.
        """
        self.__init_counters()
        for oligo in oligos:
            self._scan(oligo)
            self._total_oligos_scanned += 1
        if self._total_oligos_scanned == 0:
            raise ValueError("No oligos given to scan")
        self._has_scanned = self._total_oligos_scanned > 0
        return

    def _forward_primer_ratio(self) -> float:
        self._assert_has_scanned()
        total = sum(self._forward_primer_counter.values())
        numerator = self._forward_primer_counter[self._given_forward_primer]
        return numerator / total

    def _reverse_primer_ratio(self) -> float:
        self._assert_has_scanned()
        total = sum(self._reverse_primer_counter.values())
        numerator = self._reverse_primer_counter[self._given_reverse_primer]
        return numerator / total

    def predict_forward_primer(self) -> str:
        """
        Predict the forward primer based on the ratio of the number of times the
        given forward primer or its reverse complement is found in the oligos.

        If no primer is found, an empty string is returned.

        If the ratio is greater than 0.5, the given forward primer is returned.
        Otherwise, the reverse complement of the given forward primer is returned.
        """
        self._assert_has_scanned()
        original = self._given_forward_primer
        revcomp = self._given_forward_primer_revcomp
        func = self._forward_primer_ratio
        return self._predict_primer(original, revcomp, func)

    def predict_reverse_primer(self) -> str:
        """
        Predict the reverse primer based on the ratio of the number of times the
        given reverse primer or its reverse complement is found in the oligos.

        If no primer is found, an empty string is returned.

        If the ratio is greater than 0.5, the given reverse primer is returned.
        Otherwise, the reverse complement of the given reverse primer is returned.
        """
        self._assert_has_scanned()
        original = self._given_reverse_primer
        revcomp = self._given_reverse_primer_revcomp
        func = self._reverse_primer_ratio
        return self._predict_primer(original, revcomp, func)

    def _predict_primer(
        self, original: str, revcomp: str, func: t.Callable[[], None]
    ) -> str:
        self._assert_has_scanned()
        try:
            ratio = func()
        except ZeroDivisionError:
            # This happens when the primer is not found in any of the oligos
            primer = ""  # use empty string to indicate no primer found, let caller deal with it
        else:
            primer = original if ratio > 0.5 else revcomp
        return primer

    def _scan(self, oligo: str) -> None:
        for original, revcomp, counter in [
            (
                self._given_forward_primer,
                self._given_forward_primer_revcomp,
                self._forward_primer_counter,
            ),
            (
                self._given_reverse_primer,
                self._given_reverse_primer_revcomp,
                self._reverse_primer_counter,
            ),
        ]:
            self._count_primers(oligo, original, revcomp, counter)

    def _count_primers(
        self, oligo: str, original: str, revcomp: str, counter: t.Dict[str, int]
    ) -> None:
        if original == "" and revcomp == "":
            has_original = has_revcomp = True
        else:
            (has_original, has_revcomp) = self._find_primers(oligo, original, revcomp)
        counter[original] += 1 if has_original else 0
        counter[revcomp] += 1 if has_revcomp else 0
        return

    def _find_primers(
        self, oligo: str, original: str, revcomp: str
    ) -> t.Tuple[bool, bool]:
        has_original_at_either_end = oligo.startswith(original) or oligo.endswith(
            original
        )
        has_revcomp_at_either_end = oligo.startswith(revcomp) or oligo.endswith(revcomp)
        contains_original = original in oligo
        contains_revcomp = revcomp in oligo
        # Catch dangerous scenarios
        # Edge case 1: a primer is found but not at either end of the oligo
        has_original_not_at_ends = contains_original and not has_original_at_either_end
        has_revcomp_not_at_ends = contains_revcomp and not has_revcomp_at_either_end
        if has_original_not_at_ends or has_revcomp_not_at_ends:
            msg = "Oligo contains a primer that is not found at either end of the oligo; this is not supported at this this time."
            raise UndevelopedFeatureError(msg)

        # Edge case 2: the original and revcomp are found in the same oligo
        has_original_and_revcomp = contains_original and contains_revcomp
        if has_original_and_revcomp:
            msg = "Oligo contains both the original primer and a reverse combinant of that same primer; this is not supported at this time."
            raise UndevelopedFeatureError(msg)

        # Normal case:
        return has_original_at_either_end, has_revcomp_at_either_end

    def _assert_has_scanned(self):
        if not self._has_scanned:
            msg = "Must call 'scan_all()' before calling this method or property"
            raise RuntimeError(msg)


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

    def get_clean_reverse_complement_flag(self) -> bool:
        self._assert_has_validated_all()
        return self._get_arg(_ARG_REVERSE_COMPLEMENT_FLAG)

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

    def _validate_reverse_complement_flag(self):
        flag = self._get_arg(_ARG_REVERSE_COMPLEMENT_FLAG)
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
        help=_HELP__SKIP_N_ROWS,
        dest=_ARG_SKIP_N_ROWS,
    )

    # Include a way to toggle the output sequences to be in reverse complement, default is false
    parser.add_argument(
        "--revcomp",
        action="store_true",
        default=False,
        help=_HELP__REVERSE_COMPLEMENT_FLAG,
        dest=_ARG_REVERSE_COMPLEMENT_FLAG,
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
    reverse_complement_flag: bool,
):
    report = Report()
    input_file = Path(input_file)
    output_file = Path(output_file)
    output_headers = [
        _OUTPUT_HEADER__ID,
        _OUTPUT_HEADER__NAME,
        _OUTPUT_HEADER__SEQUENCE,
    ]

    # Scan the file once to auto-detect the best primers
    csv_helper = CSVHelper(input_file, skip_n_rows=skip_n_rows)
    with csv_helper.get_csv_reader() as csv_reader:
        primer_scanner = PrimerScanner(
            forward_primer=forward_primer, reverse_primer=reverse_primer
        )
        dict_rows = filter_rows(
            csv_reader, name_index=name_index, sequence_index=sequence_index
        )
        oligos_to_scan = [row[_OUTPUT_HEADER__SEQUENCE] for row in dict_rows]
        primer_scanner.scan_all(oligos_to_scan)
        detected_forward_primer = primer_scanner.predict_forward_primer()
        detected_reverse_primer = primer_scanner.predict_reverse_primer()
        report.add_scanning_summary(primer_scanner.summary())

    # Prepare closured functions for writing the output file
    _reverse_complement_sequences_closure = partial(
        reverse_complement_sequences,
        header=_OUTPUT_HEADER__SEQUENCE,
    )
    trim_sequences_closure = partial(
        trim_sequences,
        sequence_header=_OUTPUT_HEADER__SEQUENCE,
        id_header=_OUTPUT_HEADER__ID,
        forward_primer=detected_forward_primer,
        reverse_primer=detected_reverse_primer,
    )
    conditionally_reverse_complement_sequences = (
        _reverse_complement_sequences_closure
        if reverse_complement_flag
        else noop_sequences
    )

    # Prepare a temporary file to write to
    with tempfile.NamedTemporaryFile(delete=True) as temp_handle:
        temp_file = Path(temp_handle.name)

        # Read the input file and write to a temporary file
        csv_helper = CSVHelper(input_file, skip_n_rows=skip_n_rows)
        with csv_helper.get_csv_reader() as csv_reader:
            dict_rows = filter_rows(
                csv_reader, name_index=name_index, sequence_index=sequence_index
            )
            dict_rows = trim_sequences_closure(dict_rows, report=report)
            dict_rows = conditionally_reverse_complement_sequences(dict_rows)
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
    dict_rows: t.Iterator[t.Dict[str, str]],
    forward_primer: str,
    reverse_primer: str,
    report: Report,
    sequence_header: str,
    id_header: str,
) -> t.Iterable[t.Dict[str, str]]:
    """
    Trim the forward and reverse primer from the sequence.

    Yield dictionaries of index, name, sequence values from each row, where keys are the new headers.

    Header corresponds to the CSV header for the sequence column.
    """
    for dict_row in dict_rows:
        # Trim the sequence and update the dictionary
        sequence = dict_row[sequence_header]
        (
            trimmed_sequence,
            has_trimmed_forward_primer,
            has_trimmed_reverse_primer,
        ) = trim_sequence(sequence, forward_primer, reverse_primer)
        dict_row[sequence_header] = trimmed_sequence

        # Update the report
        row_id = dict_row[id_header]
        report.add_row(row_id, has_trimmed_forward_primer, has_trimmed_reverse_primer)
        yield dict_row


def trim_sequence(
    sequence: str, forward_primer: str, reverse_primer: str
) -> t.Tuple[str, bool, bool]:
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
        reverse_primer_exists_after_trimming = sequence[temp_index:].endswith(
            reverse_primer
        )
        is_overlapping = (
            reverse_primer_exists and not reverse_primer_exists_after_trimming
        )
        start_index = temp_index
        has_trimmed_forward_primer = True

    if reverse_primer_exists:
        temp_index = len(sequence) - len(reverse_primer)
        forward_primer_exists_after_trimming = sequence[:temp_index].startswith(
            forward_primer
        )
        is_overlapping = (
            forward_primer_exists and not forward_primer_exists_after_trimming
        )
        end_index = temp_index
        has_trimmed_reverse_primer = True

    if is_overlapping:
        raise UndevelopedFeatureError(err_msg)

    trimmed_sequence = sequence[start_index:end_index]

    return (trimmed_sequence, has_trimmed_forward_primer, has_trimmed_reverse_primer)


def reverse_complement_sequences(
    dict_rows: t.Iterator[t.Dict[str, str]],
    header: str,
) -> t.Iterable[t.Dict[str, str]]:
    """
    Update each row to have the reverse complement of the sequence.

    Header corresponds to the CSV header for the sequence column.
    """
    for dict_row in dict_rows:
        sequence = dict_row[header]
        reversed_sequence = reverse_complement(sequence)
        dict_row[header] = reversed_sequence
        yield dict_row


def noop_sequences(
    dict_rows: t.Iterator[t.Dict[str, str]]
) -> t.Iterable[t.Dict[str, str]]:
    """
    Pass through the rows without changing them.
    """
    for dict_row in dict_rows:
        yield dict_row


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


def reverse_complement(sequence: str) -> str:
    """
    Reverse complement the sequence (DNA only).
    """
    # Make the translation map
    trans = str.maketrans("ACGT", "TGCA")
    # Translate the sequence and reverse it
    return sequence.translate(trans)[::-1]


def display_error(prefix: str, error: Exception) -> None:
    """
    Display the error message.
    """
    error_msg = f"{prefix}\n{error}"
    print(error_msg, file=sys.stderr)


if __name__ == "__main__":  # noqa: C901
    if sys.version_info < (3, 8):
        display_error("Python 3.8 or newer is required.")
        sys.exit(1)
    parser = get_argparser()
    namespace = parser.parse_args()
    cleaner = ArgsCleaner(namespace)
    try:
        cleaner.validate()
    except ValidationError as err:
        display_error("Error: Argument validation!", err)
        sys.exit(1)
    except (UndevelopedFeatureError, NotImplementedError) as err:
        display_error("Error: Not implemented feature!", err)
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
        reverse_complement_flag=cleaner.get_clean_reverse_complement_flag(),
    )
