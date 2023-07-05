import typing as t
import functools
from pathlib import Path

import pytest

import numpy as np
import pandas as pd

# HELPERS


def _add_file_header(func):
    def add_file_header_wrapper(file_path: Path) -> Path:
        with open(file_path, "r") as f:
            lines = f.readlines()
        new_lines = [
            "##library-type: single\n",
            "##library-name: chr19_11027748_11027999_plus_sgRNA_SMARCA4_exon24_1162496800\n",
        ] + lines
        with open(file_path, "w") as f:
            f.writelines(new_lines)
        return file_path

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        file_path = func(*args, **kwargs)
        if kwargs.get("include_file_header", True):
            file_path = add_file_header_wrapper(file_path)
        return file_path

    return wrapper


@_add_file_header
def generate_csv_file(
    file_path: Path,
    *,  # Force keyword arguments
    seed: int = 0,
    rows: int = 10,
    columns: int = 5,
    include_file_header: bool = True,
    include_column_header: bool = True,
) -> Path:
    column_names = [f"col_{str(i)}" for i in range(columns)]
    final_column_names = column_names if include_column_header else None

    np.random.seed(seed)  # Ensure deterministic randomness
    data = np.random.rand(rows, columns)
    df = pd.DataFrame(data, columns=final_column_names)
    df.to_csv(file_path, index=False)
    return file_path


def generate_erroneous_csv_file(
    file_path: Path,
    *,  # Force keyword arguments
    seed: int = 0,
    rows: int = 10,
    columns: int = 5,
    include_file_header: bool = True,
    include_column_header: bool = True,
) -> Path:
    file_path = generate_csv_file(
        file_path,
        seed=seed,
        rows=rows,
        columns=columns,
        include_file_header=include_file_header,
        include_column_header=include_column_header,
    )

    # Alter rows 3rd, 7th and last to have 3, 6, and 6 columns respectively
    np.random.seed(seed)
    err_row_3 = list(np.random.rand(3))
    err_row_6 = list(np.random.rand(6))
    err_row_10 = list(np.random.rand(6))
    with open(file_path, "r") as f:
        lines = f.readlines()
        # If any column header or file headers are present this alters the line numbers
        # that need to be altered, so we use negative indices to count from the end.
        for idx, errors in zip([-7, -4, -1], [err_row_3, err_row_6, err_row_10]):
            lines[idx] = ",".join([str(x) for x in errors]) + "\n"
    with open(file_path, "w") as f:
        f.writelines(lines)
    return file_path


# FIXTURES


@pytest.fixture
def make_csv_file(
    tmp_path,
) -> t.Generator[t.Callable[[bool, int, bool, bool], Path], None, None]:
    """
    Make a CSV file from a callable that takes the following keyword arguments:
        is_erroneous: bool
        columns: int
        include_file_header: bool
        include_column_header: bool

    By default the CSV will have 10 rows, 5 columns, and will include both file
    and column headers.
    """
    rows = 10
    csv_file_path = tmp_path / "test.csv"

    def _make_csv_file(
        is_erroneous: bool = False,
        columns: int = 5,
        include_file_header: bool = True,
        include_column_header: bool = True,
    ) -> Path:
        maker_func = generate_erroneous_csv_file if is_erroneous else generate_csv_file
        file_path = maker_func(
            csv_file_path,
            rows=rows,
            columns=columns,
            include_file_header=include_file_header,
            include_column_header=include_column_header,
        )
        return file_path

    yield _make_csv_file
