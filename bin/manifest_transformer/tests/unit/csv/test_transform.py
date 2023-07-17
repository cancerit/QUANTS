import pytest
from src.csv import _transform
from src import constants as const


REORDER_PARAMS = [
    pytest.param(
        ["a", "b", "c"],
        [0, 1, 2],
        ["a", "b", "c"],
        id="do_nothing",
    ),
    pytest.param(
        ["a", "b", "c"],
        [2, 0, 1],
        ["c", "a", "b"],
        id="reorder",
    ),
    pytest.param(
        ["a", "b", "c", "d", "e"],
        [2, 3],
        ["c", "d"],
        id="truncate",
    ),
    pytest.param(
        ["a", "b", "c", "d", "e"],
        [3, 2],
        ["d", "c"],
        id="truncate_and_reorder",
    ),
    pytest.param(
        ["a", "b"],
        [0, 1, 2, 3, 4],
        ["a", "b"],
        id="ignore_out_of_bounds",
    ),
    pytest.param(
        [],
        [0, 1, 2],
        [],
        id="empty_row",
    ),
    pytest.param(
        ["a", "b", "c"],
        [],
        [],
        id="empty_order",
    ),
    pytest.param(
        ["a"],
        [0],
        ["a"],
        id="single_element",
    ),
]

REORDER_MANY_ROWS_PARAMS = [
    pytest.param(
        [
            ["a1", "b1", "c1"],
            ["a2", "b2", "c2"],
        ],
        [0, 1, 2],
        [
            ["a1", "b1", "c1"],
            ["a2", "b2", "c2"],
        ],
        id="do_nothing",
    ),
    pytest.param(
        [
            ["a1", "b1", "c1"],
            ["a2", "b2", "c2"],
        ],
        [2, 0, 1],
        [
            ["c1", "a1", "b1"],
            ["c2", "a2", "b2"],
        ],
        id="reorder",
    ),
    pytest.param(
        [
            ["a1", "b1", "c1", "d1", "e1"],
            ["a2", "b2", "c2", "d2", "e2"],
        ],
        [2, 3],
        [
            ["c1", "d1"],
            ["c2", "d2"],
        ],
        id="truncate",
    ),
    pytest.param(
        [
            ["a1", "b1", "c1", "d1", "e1"],
            ["a2", "b2", "c2", "d2", "e2"],
        ],
        [3, 2],
        [
            ["d1", "c1"],
            ["d2", "c2"],
        ],
        id="truncate_and_reorder",
    ),
    pytest.param(
        [
            ["a1", "b1"],
            ["a2", "b2"],
        ],
        [0, 1, 2, 3, 4],
        [
            ["a1", "b1"],
            ["a2", "b2"],
        ],
        id="ignore_out_of_bounds",
    ),
    pytest.param(
        [
            [],
            [],
        ],
        [0, 1, 2],
        [
            [],
            [],
        ],
        id="empty_row",
    ),
    pytest.param(
        [
            ["a1", "b1", "c1"],
            ["a2", "b2", "c2"],
        ],
        [],
        [
            [],
            [],
        ],
        id="empty_order",
    ),
    pytest.param(
        [
            ["a1"],
            ["a2"],
        ],
        [0],
        [
            ["a1"],
            ["a2"],
        ],
        id="single_element",
    ),
]


@pytest.mark.parametrize("row, column_index_order, expected_result", REORDER_PARAMS)
def test_reorder_row(row, column_index_order, expected_result):
    # When
    result = _transform.reorder_row(row, column_index_order)

    # Then the result should match the expected output.
    assert result == expected_result


@pytest.mark.parametrize(
    "rows, column_index_order, expected_result", REORDER_MANY_ROWS_PARAMS
)
def test_reorder_rows(rows, column_index_order, expected_result):
    # When
    result_generator = _transform.reorder_rows(rows, column_index_order)
    result = list(result_generator)

    # Then the result should match the expected output.
    assert result == expected_result


@pytest.mark.parametrize(
    "row, column_index_order",
    [
        pytest.param(
            ["a", "b", "c"],
            [-1, 0, 1],
            id="error#negative_index",
        ),
        pytest.param(
            ["a", "b", "c"],
            [0, 1, 1],
            id="error#duplicate_index",
        ),
    ],
)
def test_reorder_row__raises_error(row, column_index_order):
    # When & Then
    with pytest.raises(ValueError):
        _transform.reorder_row(row, column_index_order)


@pytest.mark.parametrize(
    "rows, column_name_remap, expected",
    [
        pytest.param(
            iter([]),
            {"a": "X", "b": "Y", "c": "Z"},
            [],
            id="reheader_zero_rows",
        ),
        pytest.param(
            iter([["a", "b", "c"]]),
            {"a": "X", "b": "Y", "c": "Z"},
            [["X", "Y", "Z"]],
            id="reheader_single_row",
        ),
        pytest.param(
            iter([["a", "b", "c"], ["d", "e", "f"]]),
            {"a": "X", "b": "Y", "c": "Z"},
            [["X", "Y", "Z"], ["d", "e", "f"]],
            id="reheader_multiple_rows",
        ),
    ],
)
def test_reheader_rows__column_names(rows, column_name_remap, expected):
    # When
    obj = _transform.ReheaderColumns(
        column_name_remap, const.SUBCOMMAND__COLUMN_NAMES, append=False
    )
    # Then
    assert list(obj.reheader_rows(rows)) == expected


@pytest.mark.parametrize(
    "rows, column_name_remap, expected",
    [
        pytest.param(
            iter([]),
            {0: "X", 1: "Y", 2: "Z"},
            [],
            id="reheader_zero_rows",
        ),
        pytest.param(
            iter([["a", "b", "c"]]),
            {0: "X", 1: "Y", 2: "Z"},
            [["X", "Y", "Z"]],
            id="reheader_single_row",
        ),
        pytest.param(
            iter([["a", "b", "c"], ["d", "e", "f"]]),
            {0: "X", 1: "Y", 2: "Z"},
            [["X", "Y", "Z"], ["d", "e", "f"]],
            id="reheader_multiple_rows",
        ),
    ],
)
def test_reheader_rows__column_indices_no_append(rows, column_name_remap, expected):
    # When
    obj = _transform.ReheaderColumns(
        column_name_remap, const.SUBCOMMAND__COLUMN_INDICES, append=False
    )

    # Then
    assert list(obj.reheader_rows(rows)) == expected


@pytest.mark.parametrize(
    "rows,column_name_remap,expected",
    [
        pytest.param(
            iter([]),
            {0: "X", 1: "Y", 2: "Z"},
            [],
            id="do_not_append_header_to_zero_rows",
        ),
        pytest.param(
            iter([["a", "b", "c"]]),
            {0: "X", 1: "Y", 2: "Z"},
            [["X", "Y", "Z"], ["a", "b", "c"]],
            id="append_header_to_single_row",
        ),
        pytest.param(
            iter([["a", "b", "c"], ["d", "e", "f"]]),
            {0: "X", 1: "Y", 2: "Z"},
            [["X", "Y", "Z"], ["a", "b", "c"], ["d", "e", "f"]],
            id="append_header_to_multiple_rows",
        ),
    ],
)
def test_reheader_rows_column__indices_append(rows, column_name_remap, expected):
    # When
    obj = _transform.ReheaderColumns(
        column_name_remap, const.SUBCOMMAND__COLUMN_INDICES, append=True
    )

    # Then
    assert list(obj.reheader_rows(rows)) == expected
