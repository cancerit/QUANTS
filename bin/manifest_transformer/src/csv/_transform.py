import typing as t


class ReorderColumns:
    """
    Reorder (and in some cases truncate) columns in a row, according to the given column index order.

    Caveats:
    - The given row is modified in-place.
    - If a given index is out-of-bounds of the row dimensions, then it is ignored.
    - If fewer indices are given than the number of columns in the row, then the row is truncated.

    Exceptions:
    - If an index is negative, then a ValueError is raised.
    - If an index is repeated, then a ValueError is raised.
    """

    def __init__(self, column_index_order: t.Iterable[int]) -> None:
        self._reorder_sequence = list(column_index_order)
        self._reorder_map: t.Dict[int, int] = self._create_reorder_map(
            self._reorder_sequence
        )

    def _create_reorder_map(self, column_index_order: t.List[int]) -> t.Dict[int, int]:
        """
        Create a map of new index to old index.
        """
        # Check for errors.
        if any(index < 0 for index in column_index_order):
            raise ValueError("Negative index.")
        if len(column_index_order) != len(set(column_index_order)):
            raise ValueError("Duplicate index.")

        # Create the map.
        reorder_map = {}
        for new_index, old_index in enumerate(column_index_order):
            reorder_map[new_index] = old_index
        return reorder_map

    def reorder(self, row: t.List[t.Any]) -> t.List[t.Any]:
        """
        Reorder (and in some cases truncate) columns in a row.
        """
        reorder_map = self._reorder_map
        new_row_length = len(self._reorder_sequence)

        if not row:
            return []
        if not new_row_length:
            return []

        new_row = []
        for new_index in range(new_row_length):
            old_index = reorder_map.get(new_index, None)
            # If the new index is out-of-bounds, then ignore it.
            if old_index is None or old_index >= len(row):
                continue
            # If the new index is in-bounds, then append the corresponding value.
            value = row[old_index]
            new_row.append(value)
        return new_row


def reorder_row(row: t.List[t.Any], column_index_order: t.List[int]) -> t.List[t.Any]:
    """
    Reorder (and in some cases truncate) columns in a row, according to the given column index order.

    Caveats:
    - The given row is modified in-place.
    - If a given index is out-of-bounds of the row dimensions, then it is ignored.
    - If fewer indices are given than the number of columns in the row, then the row is truncated.

    Exceptions:
    - If an index is negative, then a ValueError is raised.
    - If an index is repeated, then a ValueError is raised.
    """
    transformer = ReorderColumns(column_index_order)
    return transformer.reorder(row)


def reorder_rows(
    rows: t.Iterable[t.List[t.Any]], column_index_order: t.List[int]
) -> t.Generator[t.List[t.Any], None, None]:
    """
    Reorder (and in some cases truncate) columns in each row, according to the given column index order.

    Caveats:
    - The given row is modified in-place.
    - If a given index is out-of-bounds of the row dimensions, then it is ignored.
    - If fewer indices are given than the number of columns in the row, then the row is truncated.

    Exceptions:
    - If an index is negative, then a ValueError is raised.
    - If an index is repeated, then a ValueError is raised.
    """
    transformer = ReorderColumns(column_index_order)
    for row in rows:
        yield transformer.reorder(row)
