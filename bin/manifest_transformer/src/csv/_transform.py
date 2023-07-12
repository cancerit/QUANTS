import typing as t
import itertools as it
from src import constants as const


class ReheaderColumns:
    def __init__(
        self,
        column_name_remap: t.Dict[t.Union[str, int], t.Any],
        mode: str,
        append: bool,
    ):
        self._column_name_remap: t.Dict[t.Union[str, int], t.Any] = column_name_remap
        self._mode: str = mode
        self._append: bool = append
        if self._mode not in {
            const.SUBCOMMAND__COLUMN_NAMES,
            const.SUBCOMMAND__COLUMN_INDICES,
        }:
            raise NotImplementedError(f"Invalid mode: {self._mode}")
        if self._mode == const.SUBCOMMAND__COLUMN_NAMES and self._append:
            raise NotImplementedError(
                f"Invalid reheader mode: {self._mode!r} and reheader-append. It is not possible to append novel header rows when using column names."
            )

    def reheader_rows(
        self, rows: t.Iterator[t.List[t.Any]]
    ) -> t.Iterable[t.List[t.Any]]:
        """
        Apply the appropriate reheader method to the rows from an iterator based on the instance's mode and append state.

        The method modifies the first row of the input iterator according to the instance's mode and append state.
        The modified first row (or a new row, in the case of 'column_indices' mode with append=True) is then
        concatenated with the rest of the iterator into a single iterable.

        If the input iterator is empty, an empty iterator is returned.

        Args:
            rows: An iterator of rows to be reheadered. Each row is a list of items.

        Returns:
            Iterable: An iterable of reheadered rows. If append=True and mode='column_indices',
            the first row of the iterable will be a new row.

        Raises:
            NotImplementedError: If the instance's mode and append state do not match any handled conditions.
        """
        try:
            first_row = next(rows)
        except StopIteration:
            # The generator is empty, return an empty generator
            return iter([])

        result = self._reheader_rows(first_row)
        return it.chain(result, rows)

    def _reheader_rows(self, first_row: t.List[t.Any]) -> t.Iterable[t.List[t.Any]]:
        if self._mode == const.SUBCOMMAND__COLUMN_NAMES:
            result = [self._column_names__reheader(first_row)]
        elif self._mode == const.SUBCOMMAND__COLUMN_INDICES and self._append:
            new_row = self._column_indices__reheader__append(first_row)
            # itertools.chain is used to concatenate the new row, the original first row, and the rest of the generator
            # into a single iterable. It makes the new_row the first row, followed by the original first row,
            # and then the rest of the rows from the generator.
            result = [new_row, first_row]
        elif self._mode == const.SUBCOMMAND__COLUMN_INDICES and not self._append:
            result = [self._column_indices__reheader(first_row)]
        else:
            raise NotImplementedError(
                f"Unhandled condition: mode={self._mode}, append={self._append}"
            )
        return result

    def _column_names__reheader(self, row: t.List[t.Any]) -> t.List[t.Any]:
        """
        Reheader (aka relabel) the column names in a row, according to the given column name remap.

        Caveats:
        - The given row is modified in-place.
        - If a given column name is not in the row, then the column is left unchanged.
        """
        column_name_remap = self._column_name_remap
        for col_index, original_name in enumerate(row):
            if original_name in column_name_remap:
                new_name = column_name_remap[original_name]
                row[col_index] = new_name
        return row

    def _column_indices__reheader(self, row: t.List[t.Any]) -> t.List[t.Any]:
        """
        Reheader (aka relabel) the column names in a row, according to the given column name remap.

        Caveats:
        - The given row is modified in-place.
        - If a given column name is not in the row, then the column is left unchanged.
        """
        column_name_remap = self._column_name_remap
        for col_index, _ in enumerate(row):
            if col_index in column_name_remap:
                new_name = column_name_remap[col_index]
                row[col_index] = new_name
        return row

    def _column_indices__reheader__append(
        self,
        row: t.List[t.Any],
    ) -> t.List[t.Any]:
        """
        Creates a new row with the column names in a row, according to the given column name remap.

        Caveats:
        - If a given column name is not in the row, then the column is left unchanged.
        """
        column_name_remap = self._column_name_remap
        # Pad the row with placeholders, so that we can replace by index.
        new_row = [f"placeholder-{i+1}" for i in range(len(column_name_remap))]

        for col_index in range(len(row)):
            if col_index in column_name_remap:
                new_name = column_name_remap[col_index]
                new_row[col_index] = new_name
        return new_row


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
