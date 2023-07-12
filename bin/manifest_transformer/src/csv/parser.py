#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
import typing as t
import csv
from contextlib import contextmanager
from pathlib import Path
from collections import Counter

from src import constants as const
from src.enums import ColumnMode
from src.exceptions import ValidationError

if t.TYPE_CHECKING:
    import _csv
    from src.csv.properties import CSVFileProperties


class CSVParser:
    def __init__(
        self,
        file_path: Path,
        has_header: bool,
        offset: int,
        *,  # force keyword arguments
        dialect: t.Optional[csv.Dialect] = None,
        delimiter: t.Optional[str] = None,
    ) -> None:
        self._file_path = file_path
        self._offset = offset
        self._has_header = has_header
        self._columns_count = 0
        self._columns_count_comprehensively: t.Tuple[int, bool] = (0, True)
        self.__init__guard_kwargs(dialect=dialect, delimiter=delimiter)
        if dialect is not None:
            self._dialect = dialect
            self._delimiter = dialect.delimiter
            self._use_dialect = True
        elif delimiter is not None:
            self._dialect = None
            self._delimiter = delimiter
            self._use_dialect = False

    def __init__guard_kwargs(
        self, dialect: t.Optional[csv.Dialect] = None, delimiter: t.Optional[str] = None
    ) -> None:
        if dialect is None and delimiter is None:
            raise ValueError("Either dialect or delimiter must be provided.")
        elif dialect is not None and delimiter is not None:
            raise ValueError("Only one of dialect or delimiter must be provided.")

    @classmethod
    def from_csv_file_properties(
        cls, file_path: t.Union[str, Path], csv_file_properties: "CSVFileProperties"
    ) -> "CSVParser":
        offset = csv_file_properties.file_offset
        has_header = csv_file_properties.has_column_headers()
        if csv_file_properties.is_forced_delimiter():
            dialect = None
            delimiter = csv_file_properties.delimiter
        else:
            dialect = csv_file_properties.dialect
            delimiter = None
        obj = cls(
            file_path=Path(file_path),
            has_header=has_header,
            offset=offset,
            dialect=dialect,
            delimiter=delimiter,
        )
        return obj

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
            >>> with csv_helper.get_csv_reader() as reader:
            ...     for row in reader:
            ...         print(row)
        """
        with open(self._file_path, newline="") as csvfile:
            csvfile.seek(self._offset)
            if self._use_dialect:
                reader = csv.reader(csvfile, dialect=self._dialect)
            else:
                reader = csv.reader(csvfile, delimiter=self._delimiter)
            try:
                yield reader
            finally:
                pass

    def translate_column_names_to_indices(
        self, column_names: t.Iterable[str], one_index: bool = False
    ) -> t.Tuple[int, ...]:
        """
        Translate column names to column indices, in the order they are provided. The indices are 0-based.

        If a column name is not found, it is ignored and its index is not included in the returned tuple.

        column_names: The column names to translate.
        one_index: Whether to return 1-based indices.
        """
        column_names_ordered = self.column_header_names()
        increment = 1 if one_index else 0
        indices = []
        for column_name in column_names:
            try:
                index = column_names_ordered.index(column_name)
            except ValueError:
                continue
            index += increment
            indices.append(index)
        return tuple(indices)

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

    def column_header_names(self) -> t.Tuple[str, ...]:
        """
        Return the column names from the header row.

        Raises a RuntimeError if called when initialisation was CSVParser(has_header=False).
        """
        if self._has_header:
            return self._get_column_header_names()
        else:
            msg = "CSVParser was not initialized to expect a header row. Create a new CSVParser with has_header=True."
            raise RuntimeError(msg)

    def _get_column_header_names(self) -> t.Tuple[str, ...]:
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

        In an ideal case, a 2-tuple is returned with the number of columns and a
        boolean indicating whether all rows have the same number of columns
        (where True means they are all the same).
        """
        if self._columns_count_comprehensively == (0, True):
            self._columns_count_comprehensively = (
                self._get_columns_count_comprehensively()
            )
        return self._columns_count_comprehensively

    def _get_columns_count_comprehensively(self) -> t.Tuple[int, bool]:
        counter = Counter()
        row_count = 0
        with self.get_csv_reader() as reader:
            for row in reader:
                counter[len(row)] += 1
                row_count += 1
        # Explain the following code: `(counter.most_common(1)[0][0], len(counter) == 1)`
        # `counter.most_common(1)` returns a list of tuples of the form (length, count).
        # `counter.most_common(1)[0]` returns the first tuple in the list.
        if len(counter) == 0:
            column_count = 0
            same_column_count_for_all_rows = True
        else:
            column_count, row_freq = counter.most_common(1)[0]
            same_column_count_for_all_rows = row_freq == row_count
        return (column_count, same_column_count_for_all_rows)

    def find_rows_with_nulls(
        self,
        extra_null_values: t.Optional[t.List[str]] = None,
        one_index: bool = False,
    ) -> t.List[int]:
        """
        Find rows that have null values, skipping the header row if present.

        Null values:
         - '', 'N/A', 'NA', 'NAN', 'NaN', 'NULL'
         - in these cases, as well as lower, upper, and title case variants

        Args:
            extra_null_values: A list of extra null values to check for.
            one_index: Whether to return 1-based indices. By default, 0-based indices are returned.

        Returns:
            A list of row indices that are completely empty.
        """
        # Find null containing rows
        null_rows = self._find_rows_with_nulls(extra_null_values=extra_null_values)
        if one_index:
            null_rows = [row + 1 for row in null_rows]
        return null_rows

    def _find_rows_with_nulls(
        self, extra_null_values: t.Optional[t.List[str]] = None
    ) -> t.List[int]:
        # Prepare null values
        null_values: t.List[str] = const.get_null_values()
        if extra_null_values is not None:
            null_values.extend(extra_null_values)
        null_values = const.transform_to_many_cases(null_values)
        null_values_set = set(null_values)

        # Find null containing rows
        null_rows = []
        with self.get_csv_reader() as reader:
            start_idx = 0
            if self._has_header:
                next(reader)
                start_idx += 1
            for idx, row in enumerate(reader, start=start_idx):
                if any(cell in null_values_set for cell in row):
                    null_rows.append(idx)
        return null_rows


def get_column_order_as_indices(
    csv_parser: "CSVParser",
    mode: ColumnMode,
    column_order: t.Iterable[t.Union[str, int]],
) -> t.Tuple[int, ...]:
    try:
        indices = _get_column_order_as_indices(
            csv_parser=csv_parser,
            mode=mode,
            column_order=column_order,
        )
    except RuntimeError as err:
        msg = "It is very likely that the CSV file has no header row or you did set/force the correct header index."
        raise ValidationError(msg) from err
    return indices


def _get_column_order_as_indices(
    csv_parser: "CSVParser",
    mode: ColumnMode,
    column_order: t.Iterable[t.Union[str, int]],
) -> t.Tuple[int, ...]:
    if mode == ColumnMode.COLUMN_INDICES:
        column_order_as_indices = [int(elem) for elem in column_order]
    elif mode == ColumnMode.COLUMN_NAMES:
        column_names = [str(elem) for elem in column_order]
        column_order_as_indices = csv_parser.translate_column_names_to_indices(
            column_names=column_names,
            one_index=False,
        )
    else:
        raise NotImplementedError(f"Invalid mode: {mode!r}")
    return tuple(column_order_as_indices)
