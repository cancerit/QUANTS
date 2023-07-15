import typing as t
from pathlib import Path
import csv
from contextlib import contextmanager

from src.exceptions import ValidationError

if t.TYPE_CHECKING:
    import _csv


class CSVHelper:
    def __init__(
        self, file_path: Path, skip_n_rows: int, delimiter: t.Optional[str] = None
    ) -> None:
        self._file_path = file_path
        if delimiter is None:
            dialect = self._init_dialect()
            self._delimiter = dialect.delimiter
            self._dialect = dialect
        else:
            self._delimiter = delimiter
            self._dialect = None
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
            dialect_t = csv.Sniffer().sniff(sample)
            dialect = dialect_t()

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
    def get_csv_reader(self) -> t.Generator["_csv._reader", None, None]:
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
                        f"Header {header!r} not found in {str(self._file_path)!r} after searching {i+1} rows. "
                        f"Perhaps it is not there or perhaps it was over-looked because you asked to skip {self._skip_n_rows} rows."
                    )
                    raise ValueError(msg)
        raise ValueError(f"Header {header!r} not found in {str(self._file_path)!r}.")

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
        raise RuntimeError(f"Header {header!r} not found in row.")

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
        raise ValidationError("No rows found in CSV file as it is empty.")
