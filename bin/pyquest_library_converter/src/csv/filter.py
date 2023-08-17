import typing as t
import itertools

from src import constants as const
from src import cli
from src.exceptions import NullDataError


NULLS = set(const.get_null_values__all_cases())


class NullRowSplitter:
    def __init__(self, iterable: t.Iterable[t.Dict[str, str]]):
        iter1, iter2 = itertools.tee(iterable)
        self.iterable = iterable
        self.predicate = is_null_row
        self.true_queue = filter(self.predicate, iter2)
        self.false_queue = itertools.filterfalse(self.predicate, iter1)
        self.finished = False

    def null_rows(self) -> t.Iterable[t.Dict[str, str]]:
        for elem in self.true_queue:
            yield elem

    def not_null_rows(self) -> t.Iterable[t.Dict[str, str]]:
        for elem in self.false_queue:
            yield elem

    def report_null_rows(
        self,
        null_rows: t.Iterable[t.Dict[str, str]],
        raise_error: bool = True,
        start_index: int = 1,
    ) -> str:
        return report_null_rows(
            null_rows, raise_error=raise_error, start_index=start_index
        )


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
            const._OUTPUT_HEADER__ID: idx_1,
            const._OUTPUT_HEADER__NAME: name,
            const._OUTPUT_HEADER__SEQUENCE: sequence,
        }
        yield dict_row


def is_null(value: str) -> bool:
    """
    Returns True if value is a null value, False otherwise.
    """
    return value in NULLS


def is_null_row(row: t.Dict[str, str]) -> bool:
    """
    Returns True if any value in the row is a null value, False otherwise.
    """
    return any(
        is_null(value)
        for value in [
            row[const._OUTPUT_HEADER__NAME],
            row[const._OUTPUT_HEADER__SEQUENCE],
        ]
    )


def report_null_rows(
    rows: t.Iterable[t.Dict[str, str]], start_index: int, raise_error: bool
):
    """
    Returns a string of the null rows in the format:
    """
    null_original_indices = []
    for row in rows:
        new_index_1_idx = int(row[const._OUTPUT_HEADER__ID])
        orginal_index_1_idx = new_index_1_idx + start_index
        null_original_indices.append(orginal_index_1_idx)

    detail = ", ".join([str(idx) for idx in null_original_indices])
    msg = f"Null values in data rows detected for either the name or sequnce column: {detail}."
    if raise_error and null_original_indices:
        raise NullDataError(msg)
    elif null_original_indices:
        cli.display_warning(msg)
    else:
        msg = "No null values detected in data rows."
    return msg
