import typing as t

from src import constants as const


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
