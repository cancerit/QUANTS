import csv
import typing as t
from dataclasses import dataclass, field
from csv import Dialect
import functools


from pathlib import Path

_CHUNK_SIZE_1MB = 1024 * 1024
_FILE_HEADER_LINE_PREFIX = "##"


@dataclass
class CSVFileProperties:
    dialect: t.Optional[Dialect] = field(repr=False, compare=False)
    file_offset: int = field(repr=True)
    column_headers_line_index: int = field(repr=True)
    file_headers_line_indices: t.Tuple[int, ...] = field(
        default_factory=tuple,
        repr=True,
        hash=True,
    )

    def __post_init__(self):
        self.file_headers_line_indices = tuple(self.file_headers_line_indices)

    @classmethod
    def from_csv_file(
        cls,
        csv_file_path: t.Union[str, Path],
        prefix: t.Optional[str] = None,
        column_names: t.Optional[t.Sequence[str]] = None,
        delimiter: t.Optional[str] = None,
    ) -> "CSVFileProperties":
        """
        Create a CSVFileProperties object from a CSV file.

        prefix: The prefix of the file header line, typically '##'.
        column_names: Optional. If provided, it is used find the column headers
            line index, by matching the column names. If None, the column
            headers line index is searched for using a heuristic. Matching is
            more accurate than the heuristic.
            For more information, see the documentation of find_column_headers().
        delimiter: Optional. If provided, it is used to make the CSV dialect more accurate.

        """
        if prefix is None:
            prefix = _FILE_HEADER_LINE_PREFIX

        _first_line, file_offset = find_first_tabular_line_index_and_offset(
            csv_file_path, prefix=prefix
        )
        dialect = find_csv_dialect(csv_file_path, prefix=prefix, delimiters=delimiter)
        file_headers_line_indices = find_file_headers(csv_file_path, prefix=prefix)
        column_headers_line_index = find_column_headers(
            csv_file_path, prefix=prefix, column_names=column_names
        )
        obj = cls(
            dialect=dialect,
            file_offset=file_offset,
            file_headers_line_indices=file_headers_line_indices,
            column_headers_line_index=column_headers_line_index,
        )
        return obj

    @property
    def has_file_headers(self) -> bool:
        return len(self.file_headers_line_indices) > 0

    @property
    def has_column_headers(self) -> bool:
        return self.column_headers_line_index >= 0


def find_csv_dialect(
    csv_file_path: t.Union[str, Path],
    prefix: t.Optional[str] = None,
    delimiters: t.Optional[str] = None,
) -> Dialect:
    """
    Find the CSV dialect of a CSV file.

    prefix: The prefix of the file header line, typically '##'.
    delimiters: A string containing possible delimiters, e.g. ',;\t'. This is opional, as the dialect can be detected without it.
    """
    if prefix is None:
        prefix = _FILE_HEADER_LINE_PREFIX
    _, offset = find_first_tabular_line_index_and_offset(csv_file_path, prefix=prefix)
    with open(csv_file_path, newline="") as csv_file:
        csv_file.seek(offset)
        # Read the first 1MB of the file
        chunk = csv_file.read(_CHUNK_SIZE_1MB)
        dialect = csv.Sniffer().sniff(chunk, delimiters=delimiters)
    if dialect is None:
        raise ValueError("Could not detect CSV dialect")
    return dialect


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
        prefix = _FILE_HEADER_LINE_PREFIX
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
    prefix = _FILE_HEADER_LINE_PREFIX if prefix is None else prefix
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
) -> int:
    """
    Find the line index of column headers in a CSV file, by either using a heuristic
    or by searching for the index with a list of column names.

    Returns -1 if no column header line is found.

    If column_names is None, will use a heuristic to find the column headers.
    If column_names is not None, will search for the line index with the column.

    prefix: The prefix of the file header line, typically '##'.
    column_names: A list of column names to search for, or None.


    For more information, see: find_column_headers_by_heuristic and find_column_headers_by_name
    """
    prefix = _FILE_HEADER_LINE_PREFIX if prefix is None else prefix
    if column_names is None:
        idx = find_column_headers_by_heuristic(csv_file_path, prefix=prefix)
    else:
        idx = find_column_headers_by_name(csv_file_path, column_names)
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
    csv_file_path: t.Union[str, Path], prefix: t.Optional[str] = None
) -> int:
    """
    Find the line index of column headers in a CSV file, using a heuristic to
    find the most likely line index. Returns -1 if no column headers.

    Relies on CSV Sniffer to determine if the first line of the file is a
    header, and one of two key criteria will be considered to estimate if the
    sample contains a header:
    - the second through n-th rows contain numeric values
    - the second through n-th rows contain strings where at least one value's length
        differs from that of the putative header of that column.
    """
    prefix = _FILE_HEADER_LINE_PREFIX if prefix is None else prefix
    first_line, offset = find_first_tabular_line_index_and_offset(
        csv_file_path, prefix=prefix
    )
    with open(csv_file_path, newline="") as csv_file:
        csv_file.seek(offset)
        # Read the first 1MB of the file
        chunk = csv_file.read(_CHUNK_SIZE_1MB)
        # Count the number of lines in the chunk
        has_header = csv.Sniffer().has_header(chunk)
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
    prefix = _FILE_HEADER_LINE_PREFIX if prefix is None else prefix
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
