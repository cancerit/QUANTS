import typing as t
from pathlib import Path
import csv
from contextlib import contextmanager
import functools

from src.exceptions import ValidationError
from src import constants as const
from src.cli import display_warning

if t.TYPE_CHECKING:
    import _csv

_CHUNK_SIZE_1MB = 1024 * 1024
_UNSET_TABULAR_ROW_INDEX = -1000


class CSVHelper:
    def __init__(self, file_path: Path, delimiter: t.Optional[str] = None) -> None:
        self._file_path = file_path
        if delimiter is None:
            dialect = self._init_dialect()
            self._delimiter = dialect.delimiter
            self._dialect = dialect
        else:
            self._delimiter = delimiter
            self._dialect = None
        self._first_tabular_row_idx: int = _UNSET_TABULAR_ROW_INDEX
        self._first_tabular_row_offset: int = _UNSET_TABULAR_ROW_INDEX
        self._init_first_tabular_row_data()
        self._columns_count = 0
        self._line_count = 0
        self._file_structure = (0, 0, 0)
        self._header_row_0_idx = None

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

    def _init_first_tabular_row_data(self):
        self._find_first_tabular_row_idx_and_offset(one_index=False)

    def _find_first_tabular_row_idx_and_offset(
        self, one_index: bool = False
    ) -> t.Tuple[int, int]:
        """
        Find the first line index and offset of a CSV file that contains tabular
        data.

        A tabular line is defined as one that is not a file header line but can be
        either a column header line or a row data line.

        Zero indexed by default, but can be one-indexed.

        Returns:
            A tuple of the 0-indexed row index and the byte offset of the row.

        """
        # First time this method is called, find the first tabular row index and
        # offset
        if self._first_tabular_row_idx == _UNSET_TABULAR_ROW_INDEX:
            tabular_row_index, offset = find_first_tabular_line_index_and_offset(
                self._file_path,
                prefix=const.FILE_HEADER_LINE_PREFIX,
            )
            self._first_tabular_row_idx = tabular_row_index
            self._first_tabular_row_offset = offset

        # Handle one indexing
        tabular_row_index = (
            self._first_tabular_row_idx + 1
            if one_index
            else self._first_tabular_row_idx
        )
        offset = self._first_tabular_row_offset
        return (tabular_row_index, offset)

    @contextmanager
    def _get_csv_reader(self) -> t.Generator["_csv._reader", None, None]:
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
        offset = self._first_tabular_row_offset
        with open(self._file_path, newline="") as csvfile:
            csvfile.seek(offset)
            reader = (
                csv.reader(csvfile, delimiter=self._delimiter)
                if self._dialect is None
                else csv.reader(csvfile, dialect=self._dialect)
            )
            try:
                yield reader
            finally:
                pass

    def find_header_row_index(self, one_index: bool = False) -> int:
        """
        Find the row index of the first header row in a CSV file. Returns -1 if no header row is found.

        Index is 0-indexed by default, but can be 1-indexed by setting one_index=True.
        """
        header_row_index = find_column_headers(
            self._file_path, rigorous=True, column_names=None
        )
        if one_index and header_row_index != -1:
            header_row_index += 1
        return header_row_index

    def find_header_row_index_by_header(
        self, *headers: str, one_index: bool = False
    ) -> int:
        """
        Find the row index of a header in a CSV file, raising a ValidationError if it is not found.

        Index is 0-indexed by default, but can be 1-indexed by setting one_index=True.
        """
        headers_l = list(headers)
        if self._header_row_0_idx is None:
            header_row_0_idx = self._find_header_row_index_by_header(headers_l)
            self._header_row_0_idx = header_row_0_idx

        if self._header_row_0_idx == -1:
            lead = "Header" if len(headers_l) == 1 else "Headers"
            detail = ", ".join([f"{header!r}" for header in headers_l])
            msg = f"{lead} {detail!r} not found in CSV file."
            raise ValidationError(msg)

        result = self._header_row_0_idx + 1 if one_index else self._header_row_0_idx
        return result

    def _find_header_row_index_by_header(self, headers: t.List[str]) -> int:
        header_row_0_idx = find_column_headers(
            self._file_path, rigorous=True, column_names=headers
        )
        return header_row_0_idx

    def find_column_index_by_header(self, header: str, one_index: bool = False) -> int:
        """
        Find the index of a header in a CSV file, returning -1 if it is not found (even if 1-indexex).

        Index is 0-indexed by default, but can be 1-indexed by setting one_index=True.
        """
        expected_header_row_idx = self.find_header_row_index_by_header(
            header, one_index=False
        )
        first_tabular_row, _ = self._find_first_tabular_row_idx_and_offset(
            one_index=False
        )
        if first_tabular_row != expected_header_row_idx:
            first_tabular_row_1_idx = first_tabular_row + 1
            expected_header_row_1_idx = expected_header_row_idx + 1
            raise ValidationError(
                f"Header {header!r} not found in row. "
                f"Expected row index {expected_header_row_1_idx} "
                f"but first tabular row index is {first_tabular_row_1_idx}."
            )

        column_index = self._find_column_index_by_header(header)
        if column_index != -1:
            column_index += 1 if one_index else 0
        return column_index

    def _find_column_index_by_header(self, header: str) -> int:
        with self._get_csv_reader() as reader:
            row = next(reader)
            try:
                column_index = row.index(header)
            except ValueError:
                column_index = -1
            return column_index

    @property
    def columns_count(self) -> int:
        """
        Get the number of columns in the CSV file.
        """
        if self._columns_count == 0:
            self._columns_count = self._get_columns_count()
        return self._columns_count

    def _get_columns_count(self) -> int:
        with self._get_csv_reader() as reader:
            for row in reader:
                return len(row)
        raise ValidationError("No rows found in CSV file as it is empty.")

    @property
    def line_count(self) -> int:
        """
        Get the number of lines in the CSV file.
        """
        if self._line_count == 0:
            self._line_count = self._get_file_structure()
        return self._line_count

    # def get_file_structure(self) -> t.Tuple[int, int, int]:
    #     """
    #     Get the number of file header rows, column header rows, and data rows in the CSV file.
    #     """
    #     if self._file_structure == (0, 0, 0):
    #         self._file_structure = self._get_file_structure()
    #     return self._file_structure

    # def _get_file_structure(self) -> t.Tuple[int, int, int]:
    #     line_count = 0
    #     file_header_rows = 0
    #     first_tabular_row_idx = None
    #     with open(self._file_path) as file:
    #         for line in file.read():
    #             line_count += 1

    #             # Find any file header rows
    #             if line.startswith(FILE_HEADER_PREFIX):
    #                 file_header_rows += 1
    #                 continue

    #             # Find the first tabular row
    #             if first_tabular_row_idx is None and line.strip():
    #                 first_tabular_row_idx = line_count
    #                 continue


def find_file_headers(
    csv_file_path: t.Union[str, Path],
    prefix: t.Optional[str] = None,
    max_line: t.Optional[int] = 20,
) -> t.List[int]:
    """
    Find the line indices of file headers in a CSV file.

    prefix: The prefix of the file header line, typically '##'.
    max_line: The maximum number of lines to read from the CSV file, if None, read the entire file.
    """
    if prefix is None:
        prefix = const.FILE_HEADER_LINE_PREFIX
    with open(csv_file_path, "r") as csv_file:
        file_header_indices = _find_file_headers(
            csv_file, prefix=prefix, max_line=max_line
        )
    return file_header_indices


def _find_file_headers(
    csv_file: t.TextIO,
    prefix: t.Optional[str] = None,
    max_line: t.Optional[int] = 20,
) -> t.List[int]:
    prefix = const.FILE_HEADER_LINE_PREFIX if prefix is None else prefix
    file_header_indices = []
    line_idx = 0
    while True:
        line = csv_file.readline()
        if not line:
            break
        if line.startswith(prefix):
            file_header_indices.append(line_idx)
        line_idx += 1
        if max_line is not None and line_idx >= max_line:
            break
    return file_header_indices


def find_column_headers(
    csv_file_path: t.Union[str, Path],
    column_names: t.Optional[t.Sequence[str]] = None,
    prefix: t.Optional[str] = None,
    rigorous: bool = False,
) -> int:
    """
    Find the line index of column headers in a CSV file, by either using a heuristic algorith,
    or a sting matching algorithm.

    Returns -1 if no column header line is found.

    Algorithm selection:
    - If column_names is None, will use a heuristic algortithm.
    - If column_names is not None, will use a sting matching algorithm.
    - If column_names is not None and rigorous is True, will use a string
      matching algorithm and failing that, a heuristic algorithm.

    prefix: The prefix of the file header line, typically '##'.
    column_names: A list of column names to search for, or None.
    rigorous: If True, multiple algorithms will be used to find the column headers.

    For more information, see: find_column_headers_by_heuristic and find_column_headers_by_name
    """
    prefix = const.FILE_HEADER_LINE_PREFIX if prefix is None else prefix
    if column_names is None:
        idx = find_column_headers_by_heuristic(csv_file_path, prefix=prefix)
        warning_msg = const.WARN__NO_HEADERS_FOUND__HEURISTIC
    else:
        idx = find_column_headers_by_name(csv_file_path, column_names)
        warning_msg = const.WARN__NO_HEADERS_FOUND__STRING_MATCHING
        if idx == -1 and rigorous:
            # Try again with the heuristic algorithm, any errors will be
            # suppressed and idx will be -1
            suppress_error = True
            idx = find_column_headers_by_heuristic(
                csv_file_path,
                prefix=prefix,
                _suppress_csv_lib_errors=suppress_error,
            )
            warning_msg = const.WARN__NO_HEADERS_FOUND__BOTH_ALGORITHMS

    if idx == -1:
        display_warning(warning_msg)
    return idx


def find_column_headers_by_name(
    csv_file_path: t.Union[str, Path],
    column_names: t.Sequence[str],
    max_line: t.Optional[int] = 20,
    case_sensitive: bool = True,
) -> int:
    """
    Find the line index of column headers in a CSV file, using a list of column
    names to find the most likely line index. Returns -1 if no column headers

    Not all column names need to be present in the CSV file, but the more column
    names that are present, the more likely it will be correctly identified.
    Thus supplying about 3 or more column names is recommended.

    If the column names are combined with row data values (e.g. 'ref:hg38' where
    'ref' is a column name), will lead to incorrect results.

    column_names: A list of column names to search for.
    max_line: The maximum number of lines to read from the CSV file, if None,
    read the entire file.
    case_sensitive: Whether to perform case sensitive matching of column names.
    """
    with open(csv_file_path, "r") as csv_file:
        idx = _find_column_headers_by_name(
            csv_file,
            column_names=column_names,
            max_line=max_line,
            case_sensitive=case_sensitive,
        )
    return idx


def _find_column_headers_by_name(
    csv_file: t.TextIO,
    column_names: t.Sequence[str],
    max_line: t.Optional[int] = 20,
    case_sensitive: bool = False,
) -> int:
    column_names = column_names if case_sensitive else [n.lower() for n in column_names]
    scores = {}
    line_idx = 0
    while True:
        line = csv_file.readline()
        # Break if EOF or max_line reached
        if not line or (max_line is not None and line_idx >= max_line):
            break
        line = line if case_sensitive else line.lower()
        score = [1 for column_name in column_names if column_name in line]
        scores[line_idx] = sum(score)
        # Increment line index
        line_idx += 1

    # Return the first line index with the highest score, i.e. the most likely line index
    # otherwise return -1 if no column headers found.
    ascending_idxs = sorted(scores.items(), key=lambda x: x[0])
    first_best_idx, max_score = max(ascending_idxs, key=lambda x: x[1]) if scores else 0
    best_idx = first_best_idx if max_score else -1
    return best_idx


def find_column_headers_by_heuristic(
    csv_file_path: t.Union[str, Path],
    prefix: t.Optional[str] = None,
    _suppress_csv_lib_errors: bool = False,
) -> int:
    """
    Find the line index of column headers in a CSV file, using a heuristic to
    find the most likely line index. Returns -1 if no column headers.

    Relies on CSV Sniffer to determine if the first line of the file is a
    header, and one of two key criteria will be considered to estimate if the
    sample contains a header: - the second through n-th rows contain numeric
    values - the second through n-th rows contain strings where at least one
    value's length
        differs from that of the putative header of that column.

    In most cases you do no want to suppress errors but if you do the return
    value will be -1.
    """
    prefix = const.FILE_HEADER_LINE_PREFIX if prefix is None else prefix
    first_line, offset = find_first_tabular_line_index_and_offset(
        csv_file_path, prefix=prefix
    )
    with open(csv_file_path, newline="") as csv_file:
        csv_file.seek(offset)
        # Read the first 1MB of the file
        chunk = csv_file.read(_CHUNK_SIZE_1MB)
        # Count the number of lines in the chunk
        try:
            has_header = csv.Sniffer().has_header(chunk)
        except csv.Error as e:
            if not _suppress_csv_lib_errors:
                raise e
            else:
                has_header = False
    return first_line if has_header else -1


@functools.lru_cache(maxsize=32)
def find_first_tabular_line_index_and_offset(
    csv_file_path: t.Union[str, Path], prefix: t.Optional[str] = None
) -> t.Tuple[int, int]:
    """
    Find the first line index and offset of a CSV file that contains tabular
    data.

    A tabular line is defined as one that is not a file header line but can be
    either a column header line or a row data line.

    csv_file_path: The path to the CSV file. prefix: The prefix of any file
    header line, typically '##'.
    """
    prefix = const.FILE_HEADER_LINE_PREFIX if prefix is None else prefix
    file_header_idxs = find_file_headers(csv_file_path, prefix=prefix)
    stop_row_idx = max(file_header_idxs) + 1 if file_header_idxs else 0  # 0-indexed

    offset = 0
    result_offset = None

    current_row_idx = 0  # 0-indexed
    with open(csv_file_path, newline="") as csv_file:
        while True:
            line = csv_file.readline()
            offset = csv_file.tell() - len(line)
            if stop_row_idx == current_row_idx:
                result_idx = current_row_idx
                result_offset = offset
                break
            current_row_idx += 1

    if result_offset is None:
        # This should never happen
        msg = (
            f"File {csv_file_path!r} cannot calculate the offset, "
            f"because more rows were skipped ({stop_row_idx}) "
            f"than there are in the file ({current_row_idx})."
        )
        raise ValueError(msg)
    return result_idx, result_offset
