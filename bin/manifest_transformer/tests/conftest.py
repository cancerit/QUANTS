import typing as t
import functools
from pathlib import Path

import pytest

import numpy as np
import pandas as pd

from tests.test_data import files

# HELPERS


# CONSTANTS
_EXAMPLE_CSV = files.example_csv_1_with_column_headers()


def json_params__column_names() -> t.Dict[str, t.Any]:
    json_like_data = {
        "mode": "column-names",
        "input_file": str(_EXAMPLE_CSV),
        "output_file": "example_data_1_w_column_headers.output.csv",
        "summary_file": "example_data_1_w_column_headers.summary.json",
        "column_order": [
            "oligo_name",
            "species",
            "assembly",
            "gene_id",
            "transcript_id",
            "src_type",
            "ref_chr",
            "ref_strand",
            "ref_start",
            "ref_end",
        ],
        "required_columns": [
            "oligo_name",
            "species",
            "assembly",
            "gene_id",
            "transcript_id",
        ],
        "optional_columns": [
            "src_type",
            "ref_chr",
            "ref_strand",
            "ref_start",
            "ref_end",
        ],
        "reheader_mapping": {
            "oligo_name": "OLIGO_NAME",
            "species": "SPECIES",
            "assembly": "ASSEMBLY",
            "gene_id": "GENE_ID",
        },
        "output_file_delimiter": ",",
        "forced_input_file_delimiter": None,
        "forced_header_row_index": None,
    }
    return json_like_data.copy()


def json_params__column_indices() -> t.Dict[str, t.Any]:
    json_like_data = {
        "mode": "column-indices",
        "input_file": str(_EXAMPLE_CSV),
        "output_file": "example_data_1_w_column_headers.output.csv",
        "summary_file": "example_data_1_w_column_headers.summary.json",
        "column_order": [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
        ],
        "required_columns": [
            1,
            2,
            3,
            4,
            5,
        ],
        "optional_columns": [
            6,
            7,
            8,
            9,
            10,
        ],
        "reheader_mapping": {
            "1": "OLIGO_NAME",
            "2": "SPECIES",
            "3": "ASSEMBLY",
            "4": "GENE_ID",
        },
        "output_file_delimiter": ",",
        "forced_input_file_delimiter": None,
        "forced_header_row_index": None,
    }
    return json_like_data.copy()


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
    delimiter: t.Optional[str] = None,
    include_file_header: bool = True,
    include_column_header: bool = True,
    include_null_values: bool = False,
    null_value: t.Optional[str] = None,
) -> Path:
    """
    Generates a CSV file with specified parameters at the given file path.

        file_path (Path): Path where the CSV file will be written.
        seed: Seed for the random generator. Defaults to 0.
        rows: Number of rows in the CSV file. Defaults to 10.
        delimiter: The delimiter to use when serializing the csv. Defaults to ",".
        columns: Number of columns in the CSV file. Defaults to 5.
        include_file_header: If True, includes a file header. Defaults to True.
        include_column_header: If True, includes a column header. Defaults to True.
        include_null_values: If True, includes Null values in some float fields. Defaults to False.
        null_value: The string to represent Null values in the csv when serialized. Defaults to "NA".
    """
    if null_value is None:
        null_value = "NA"
    if delimiter is None:
        delimiter = ","

    column_names = [f"col_{str(i)}" for i in range(columns)]
    final_column_names = column_names if include_column_header else None

    np.random.seed(seed)  # Ensure deterministic randomness
    data = np.random.rand(rows, columns)
    if include_null_values:
        # Randomly replace some data entries with np.NaN: around 20% of your data to be null
        mask = np.random.choice([True, False], size=data.shape, p=[0.2, 0.8])

        data = np.where(mask, np.NaN, data)

    df = pd.DataFrame(data, columns=final_column_names)

    df.to_csv(
        file_path,
        index=False,
        na_rep=null_value,
        sep=delimiter,
        header=include_column_header,
    )
    return file_path


def generate_erroneous_csv_file(
    file_path: Path,
    *,  # Force keyword arguments
    seed: int = 0,
    rows: int = 10,
    columns: int = 5,
    delimiter: t.Optional[str] = None,
    include_file_header: bool = True,
    include_column_header: bool = True,
    include_null_values: bool = False,
    null_value: t.Optional[str] = None,
) -> Path:
    """
    Generates a CSV file with specified parameters at the given file path, but with
    some errors in the file, namely: the 3rd row has 3 columns, the 7th row has 6
    columns, and the last row has 6 columns.

        file_path (Path): Path where the CSV file will be written.
        seed: Seed for the random generator. Defaults to 0.
        rows: Number of rows in the CSV file. Defaults to 10.
        columns: Number of columns in the CSV file. Defaults to 5.
        delimiter: The delimiter to use when serializing the csv. Defaults to ",".
        include_file_header: If True, includes a file header. Defaults to True.
        include_column_header: If True, includes a column header. Defaults to True.
        include_null_values: If True, includes Null values in some float fields. Defaults to False.
        null_value: The string to represent Null values in the csv when serialized. Defaults to "NA".
    """
    file_path = generate_csv_file(
        file_path,
        seed=seed,
        rows=rows,
        columns=columns,
        delimiter=delimiter,
        include_file_header=include_file_header,
        include_column_header=include_column_header,
        include_null_values=include_null_values,
        null_value=null_value,
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
def make_json_file(
    tmp_path: Path,
) -> t.Generator[t.Callable[[t.Dict[str, t.Any]], Path], None, None]:
    import json

    json_file = tmp_path / "json_params.json"

    def _make_json_params(json_like_data: t.Dict[str, t.Any]) -> Path:
        with open(json_file, "w") as f:
            json.dump(json_like_data, f)
        return json_file

    yield _make_json_params


@pytest.fixture
def make_json_cmd(
    make_json_file,
) -> t.Generator[t.Callable[[t.Dict[str, t.Any]], t.List[str]], None, None]:
    def _make_json_cmd(json_like_data: t.Dict[str, t.Any]) -> t.List[str]:
        json_file = make_json_file(json_like_data)
        cmd = f"json {str(json_file)}".split()
        return cmd

    yield _make_json_cmd


@pytest.fixture
def make_csv_file(
    tmp_path,
) -> t.Generator[
    t.Callable[[bool, int, str, bool, bool, bool, t.Optional[str]], Path], None, None
]:
    """
    Make a CSV file from a callable that takes the following keyword arguments:
        is_erroneous: If True, generates an erroneous CSV file. Defaults to False.
        columns: Number of columns in the CSV file. Defaults to 5.
        delimiter: The delimiter to use when serializing the csv. Defaults to ",".
        include_file_header: If True, includes a file header. Defaults to True.
        include_column_header: If True, includes a column header. Defaults to True.
        include_null_values: If True, includes Null values in some float fields. Defaults to False.
        null_value: The string to represent Null values in the csv when serialized. Defaults to "NA".

    By default the CSV will have 10 rows, 5 columns, and will include both file
    and column headers.
    """
    rows = 10
    csv_file_path = tmp_path / "test.csv"

    def _make_csv_file(
        is_erroneous: bool = False,
        columns: int = 5,
        delimiter: t.Optional[str] = None,
        include_file_header: bool = True,
        include_column_header: bool = True,
        include_null_values: bool = False,
        null_value: t.Optional[str] = None,
    ) -> Path:
        maker_func = generate_erroneous_csv_file if is_erroneous else generate_csv_file
        file_path = maker_func(
            csv_file_path,
            rows=rows,
            columns=columns,
            delimiter=delimiter,
            include_file_header=include_file_header,
            include_column_header=include_column_header,
            include_null_values=include_null_values,
            null_value=null_value,
        )
        return file_path

    yield _make_csv_file
