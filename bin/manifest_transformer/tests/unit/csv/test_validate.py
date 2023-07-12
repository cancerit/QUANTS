import pytest

from src.csv import _validate


@pytest.mark.parametrize(
    "user_columns, reference_columns, expected_missing_columns",
    [
        pytest.param(
            ["a", "b", "c", "d"],
            ["a", "b", "c", "d"],
            [],
            id="no_missing_columns",
        ),
        pytest.param(
            ["a", "b", "c"],
            ["a", "b", "c", "d"],
            ["d"],
            id="one_missing_column",
        ),
        pytest.param(
            ["b"],
            ["a", "b", "c", "d"],
            ["a", "c", "d"],
            id="three_missing_columns",
        ),
        pytest.param(
            [],
            ["a", "b", "c", "d"],
            ["a", "b", "c", "d"],
            id="all_missing_columns",
        ),
        pytest.param(
            ["a", "b", "c", "d"],
            ["a", "b", "c"],
            [],
            id="one_extra_column",
        ),
    ],
)
def test_find_missing_columns(
    user_columns, reference_columns, expected_missing_columns
):
    # When
    actual_missing_columns = _validate.find_missing_columns(
        user_columns=user_columns,
        file_columns=reference_columns,
    )

    # Then
    assert actual_missing_columns == expected_missing_columns
