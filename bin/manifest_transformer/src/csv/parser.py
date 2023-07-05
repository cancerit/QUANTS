#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
import typing as t
import csv
from contextlib import contextmanager
from pathlib import Path
from collections import Counter

if t.TYPE_CHECKING:
    import _csv


class CSVParser:
    def __init__(
        self,
        file_path: Path,
        dialect: csv.Dialect,
        has_header: bool,
        offset: int,
    ) -> None:
        self._file_path = file_path
        self._dialect = dialect
        self._offset = offset
        self._has_header = has_header
        self._columns_count = 0
        self._header_row_tup: t.Optional[t.Tuple[int, str]] = None
        self._columns_count_comprehensively: t.Tuple[int, bool] = (0, True)

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
            csvfile.seek(self._offset)
            reader = csv.reader(csvfile, dialect=self._dialect)

            try:
                yield reader
            finally:
                pass

    def column_indices(
        self, one_index: bool = False, comprehensive: bool = False
    ) -> t.Tuple[int, ...]:
        """
        Return the column indices for the CSV file. The indices are 0-based.

        one_index: Whether to return 1-based indices.
        comprehensive: A stricter method of getting the column indices, but slower.
        """
        if comprehensive:
            column_count, uniform = self.count_columns_comprehensively()
            if not uniform:
                raise ValueError("CSV file has rows with different number of columns.")
        else:
            column_count = self.count_columns()
        indices = (
            tuple(range(1, column_count + 1))
            if one_index
            else tuple(range(column_count))
        )
        return indices

    def header_column_names(self) -> t.Tuple[str, ...]:
        """
        Return the column names from the header row.

        Raises a RuntimeError if called when initialisation was CSVParser(has_header=False).
        """
        if self._has_header:
            return self._get_header_column_names()
        else:
            msg = "CSVParser was not initialized to expect a header row. Create a new CSVParser with has_header=True."
            raise RuntimeError(msg)

    def _get_header_column_names(self) -> t.Tuple[str, ...]:
        with self.get_csv_reader() as reader:
            header_row = next(reader)
            return tuple(header_row)

    def count_columns(self) -> int:
        """
        Count the number of columns in the CSV file, using just the first row.
        """
        if self._columns_count == 0:
            self._columns_count = self._get_columns_count()
        return self._columns_count

    def _get_columns_count(self) -> int:
        with self.get_csv_reader() as reader:
            length = 0
            for row in reader:
                length = len(row)
                break
        return length

    def count_columns_comprehensively(self) -> t.Tuple[int, bool]:
        """
        Count the number of columns in the CSV file, iterating over all rows.

        This method is slower than count_columns(), but more accurate.

        In an ideal case, a 2-tuple is returned with the number of columns and
        a boolean indicating whether all rows have the same number of columns.
        """
        if self._columns_count_comprehensively == (0, True):
            self._columns_count_comprehensively = (
                self._get_columns_count_comprehensively()
            )
        return self._columns_count_comprehensively

    def _get_columns_count_comprehensively(self) -> t.Tuple[int, bool]:
        counter = Counter()
        with self.get_csv_reader() as reader:
            for row in reader:
                counter[len(row)] += 1
        return (counter.most_common(1)[0][0], len(counter) == 1)
