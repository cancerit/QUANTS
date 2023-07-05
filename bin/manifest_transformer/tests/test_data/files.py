from functools import wraps
from pkg_resources import resource_filename
from pathlib import Path

"""
This file contains functions that return the paths to the example data files.

You can import the functions individually or import the whole module, but it
will be more convenient to import do
>>> from tests import test_data
>>> test_data.files.example_data_1_csv()
"""


def _file_exists(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        file: Path = func(*args, **kwargs)
        if not file.exists():
            raise FileNotFoundError(f"File {file} does not exist")
        return file

    return wrapper


@_file_exists
def example_csv_1_with_column_headers() -> Path:
    return Path(resource_filename(__name__, "example_data_1_w_column_headers.csv"))


@_file_exists
def example_csv_1_without_headers() -> Path:
    return Path(resource_filename(__name__, "example_data_1_wo_headers.csv"))


@_file_exists
def example_tsv_2_with_column_headers() -> Path:
    return Path(resource_filename(__name__, "example_data_2_w_column_headers.tsv"))


@_file_exists
def example_tsv_2_with_file_and_column_headers() -> Path:
    return Path(resource_filename(__name__, "example_data_2_w_file+column_headers.tsv"))


@_file_exists
def example_tsv_2_without_headers() -> Path:
    return Path(resource_filename(__name__, "example_data_2_wo_headers.tsv"))


@_file_exists
def example_csv_3_with_column_headers() -> Path:
    return Path(resource_filename(__name__, "example_data_3_w_column_headers.csv"))


@_file_exists
def example_csv_3_with_file_and_column_headers() -> Path:
    return Path(resource_filename(__name__, "example_data_3_w_file+column_headers.csv"))


@_file_exists
def example_csv_3_without_headers() -> Path:
    return Path(resource_filename(__name__, "example_data_3_wo_headers.csv"))
