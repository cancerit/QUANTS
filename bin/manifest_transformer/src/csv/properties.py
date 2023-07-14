import csv
import typing as t
from dataclasses import dataclass, field
from csv import Dialect
import functools
from pathlib import Path

from src.exceptions import DelimiterError, UserInterventionRequired
from src import constants as const
from src.enums import ColumnMode
from src.cli import display_warning

if t.TYPE_CHECKING:
    from src.args._struct import CleanArgs

_CHUNK_SIZE_1MB = 1024 * 1024


@dataclass
class CSVFileProperties:
    dialect: t.Optional[Dialect] = field(repr=False, compare=False)
    _delimiter: str = field(repr=False, compare=False)
    file_offset: int = field(repr=True)
    column_headers_line_index: int = field(repr=True)
    _forced_column_headers: bool = field(repr=False, compare=False)
    file_headers_line_indices: t.Tuple[int, ...] = field(
        default_factory=tuple,
        repr=True,
        hash=True,
    )

    def __post_init__(self):
        self.file_headers_line_indices = tuple(self.file_headers_line_indices)

    def is_forced_delimiter(self) -> bool:
        """
        Return True if the delimiter was forced, False if it was programmatically detected.

        If the delimiter was forced, it is not guaranteed to be the correct
        delimiter. This may come arise from the Python CSV sniffer not being
        able to detect the delimiter and falling back to the delimeter specified
        by the user.
        """
        return self.dialect is None

    def is_forced_column_headers_line_index(self) -> bool:
        """
        Return True if the column headers line index was forced, False if it was programmatically detected.
        """
        return self._forced_column_headers

    @property
    def delimiter(self) -> str:
        return self._delimiter

    def has_file_headers(self) -> bool:
        return len(self.file_headers_line_indices) > 0

    def has_column_headers(self) -> bool:
        return self.column_headers_line_index >= 0

    @classmethod
    def from_clean_args(cls, clean_args: "CleanArgs") -> "CSVFileProperties":
        struct = (
            clean_args.copy_as_0_indexed() if clean_args.is_1_indexed else clean_args
        )
        return cls._from_clean_args(struct)

    @classmethod
    def _from_clean_args(cls, clean_args: "CleanArgs") -> "CSVFileProperties":
        if clean_args.is_1_indexed == True:
            msg = "This private method should only be called with 1-indexed CleanArgs objects"
            raise RuntimeError(msg)

        if clean_args.mode == ColumnMode.COLUMN_NAMES:
            # We use the `required_columns`` as the source of column names, not the
            # `column_order` value as it is a stronger source of columns.
            column_names = [str(elem) for elem in clean_args.required_columns]
            column_names = column_names if column_names else None
            csv_file_properties = CSVFileProperties.from_csv_file(
                csv_file_path=clean_args.input_file,
                column_names=column_names,
                forced_delimiter=clean_args.forced_input_file_delimiter,
                forced_column_headers_line_index=clean_args.forced_header_row_index,
            )
        elif clean_args.mode == ColumnMode.COLUMN_INDICES:
            column_names = None  # Column names are not available for this mode.
            csv_file_properties = CSVFileProperties.from_csv_file(
                csv_file_path=clean_args.input_file,
                column_names=column_names,
                forced_delimiter=clean_args.forced_input_file_delimiter,
                forced_column_headers_line_index=clean_args.forced_header_row_index,
            )
        else:
            raise NotImplementedError(f"Unknown mode: {clean_args.mode}")
        return csv_file_properties

    @classmethod
    def from_csv_file(
        cls,
        csv_file_path: t.Union[str, Path],
        prefix: t.Optional[str] = None,
        column_names: t.Optional[t.Sequence[str]] = None,
        forced_delimiter: t.Optional[str] = None,
        forced_column_headers_line_index: t.Optional[int] = None,
    ) -> "CSVFileProperties":
        """
        Create a CSVFileProperties object from a CSV file.

        prefix: The prefix of the file header line, typically '##'.
        column_names: Optional. If provided, it is used find the column headers
            line index, by matching the column names. If None, the column
            headers line index is searched for using a heuristic. Matching is
            more accurate than the heuristic.
            For more information, see the documentation of find_column_headers().
        forced_delimiter: Optional. If provided, it is used to make the CSV
            dialect more accurate or in case the delimiter cannot be detected it
            will coerces the delimiter.
        forced_column_headers_line_index: Optional. If provided, it will coerce headers
            line index rather than using the heuristic or matching methods to find
            the headers line index.
        """
        if prefix is None:
            prefix = const.FILE_HEADER_LINE_PREFIX

        _first_line, file_offset = find_first_tabular_line_index_and_offset(
            csv_file_path, prefix=prefix
        )

        dialect, safe_delimiter = cls._get_safe_dialect_and_delimeter(
            csv_file_path, prefix=prefix, forced_delimiter=forced_delimiter
        )

        (
            safe_column_headers_line_index,
            _forced_column_headers,
        ) = cls._get_safe_column_headers(
            csv_file_path,
            prefix=prefix,
            column_names=column_names,
            forced_index=forced_column_headers_line_index,
        )

        file_headers_line_indices = tuple(
            find_file_headers(csv_file_path, prefix=prefix)
        )

        obj = cls(
            dialect=dialect,
            _delimiter=safe_delimiter,
            file_offset=file_offset,
            file_headers_line_indices=file_headers_line_indices,
            _forced_column_headers=_forced_column_headers,
            column_headers_line_index=safe_column_headers_line_index,
        )
        return obj

    @staticmethod
    def _get_safe_dialect_and_delimeter(
        csv_file_path: t.Union[str, Path],
        prefix: str,
        forced_delimiter: t.Optional[str],
    ) -> t.Tuple[t.Optional[Dialect], str]:
        """
        Return the dialect and delimiter, or the forced delimiter if the dialect cannot be detected.
        """
        try:
            dialect = find_csv_dialect(
                csv_file_path, prefix=prefix, delimiters=forced_delimiter
            )
            safe_delimiter = dialect.delimiter
        except DelimiterError as err:
            if forced_delimiter is None:
                msg = f"{str(err)} You must force the delimiter. See --help for more information."
                raise UserInterventionRequired(msg) from None
            else:
                dialect = None
                safe_delimiter = forced_delimiter
        return dialect, safe_delimiter

    @staticmethod
    def _get_safe_column_headers(
        csv_file_path: t.Union[str, Path],
        prefix: str,
        column_names: t.Optional[t.Sequence[str]],
        forced_index: t.Optional[int],
    ) -> t.Tuple[int, bool]:
        """
        Return the column headers line index and whether the value was forced.
        """
        if forced_index is not None:
            return (forced_index, True)

        try:
            column_headers_line_index = find_column_headers(
                csv_file_path,
                prefix=prefix,
                column_names=column_names,
                rigorous=True,
            )
        except csv.Error:
            msg = (
                "It is not possible to identify the column headers line index, "
                "as the CSV delimiter could not be detected. You must force the header line index. "
                "See --help for more information."
            )
            raise UserInterventionRequired(msg) from None
        return (column_headers_line_index, False)


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
        prefix = const.FILE_HEADER_LINE_PREFIX
    _, offset = find_first_tabular_line_index_and_offset(csv_file_path, prefix=prefix)
    dialect = _find_csv_dialect(csv_file_path, offset=offset, delimiters=delimiters)
    return dialect


def _find_csv_dialect(
    csv_file_path: t.Union[str, Path],
    offset: int,
    delimiters: t.Optional[str] = None,
) -> Dialect:  # noqa: C901
    err_msg = f"Could not determine CSV delimeter for file {str(csv_file_path)!r}"
    if delimiters is None:
        err_msg = f"{err_msg}. Please provide a possible delimiter."
    else:
        err_msg = f"{err_msg} despite tying delimiters {delimiters!r}. This suggests that the file is not a tabular file or the file has a syntax error (e.g. differing numbers of column counts across many rows)."
    try:
        with open(csv_file_path, newline="") as csv_file:
            csv_file.seek(offset)
            # Read the first 1MB of the file
            chunk = csv_file.read(_CHUNK_SIZE_1MB)
            dialect = csv.Sniffer().sniff(chunk, delimiters=delimiters)
    except csv.Error as e:
        raise DelimiterError(err_msg) from e
    if dialect is None:
        raise DelimiterError(err_msg)
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
        display_warning(const.WARN__NO_HEADERS_FOUND__HEURISTIC)
    else:
        idx = find_column_headers_by_name(csv_file_path, column_names)
        if idx == -1 and rigorous:
            # Try again with the heuristic algorithm, any errors will be
            # suppressed and idx will be -1
            suppress_error = True
            idx = find_column_headers_by_heuristic(
                csv_file_path,
                prefix=prefix,
                _suppress_csv_lib_errors=suppress_error,
            )
            display_warning(const.WARN__NO_HEADERS_FOUND__BOTH_ALGORITHMS)
        elif idx == -1:
            display_warning(const.WARN__NO_HEADERS_FOUND__STRING_MATCHING)
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
