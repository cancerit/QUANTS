import typing as t
from pathlib import Path
import csv
from contextlib import contextmanager


if t.TYPE_CHECKING:
    import _csv

_CHUNK_SIZE_1MB = 1024 * 1024


class CSVReaderFactory:
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
            >>> with csv_helper.get_csv_reader() as reader:
            ...     for row in reader:
            ...         print(row)
        """
        with open(self._file_path, newline="") as csvfile:
            reader = (
                csv.reader(csvfile, delimiter=self._delimiter)
                if self._dialect is None
                else csv.reader(csvfile, dialect=self._dialect)
            )
            # Wind the reader forward by the number of rows to skip
            for _ in range(self._skip_n_rows):
                next(reader, None)  # Avoid StopIteration here
            try:
                yield reader
            finally:
                pass
