import typing as t
from pathlib import Path

import pytest

from src.args import _parser
from src.args import _struct
from src.enums import ColumnMode
from src.exceptions import ValidationError
from src import constants as const

from tests.test_data import files
from tests.conftest import json_params__column_names, json_params__column_indices

# CONSTANTS
EXAMPLE_CSV = files.example_csv_1_with_column_headers()


# TESTS


def test_CleanArgs__with_null_json_input_file():
    # Given
    cmd = "json does-not-exist.json"

    # When/Then
    argparser = _parser.get_argparser()
    namespace = argparser.parse_args(cmd.split())
    with pytest.raises(ValidationError):
        _struct.CleanArgs.from_namespace(namespace)


@pytest.mark.parametrize(
    "json_param_func", [json_params__column_names, json_params__column_indices]
)
def test_CleanArgs__with_null_input__raises_error(json_param_func, make_json_cmd):
    # Given
    input_file = None
    json_params = json_param_func()
    json_params["input_file"] = input_file
    cmd = make_json_cmd(json_params)

    # When/Then
    argparser = _parser.get_argparser()
    namespace = argparser.parse_args(cmd)
    with pytest.raises(ValidationError):
        _struct.CleanArgs.from_namespace(namespace)


@pytest.mark.parametrize(
    "json_param_func", [json_params__column_names, json_params__column_indices]
)
def test_CleanArgs__with_null_output(json_param_func, make_json_cmd):
    # Given
    json_params = json_param_func()
    json_params["output_file"] = None
    cmd = make_json_cmd(json_params)

    # When
    argparser = _parser.get_argparser()
    namespace = argparser.parse_args(cmd)
    with pytest.raises(ValidationError):
        _struct.CleanArgs.from_namespace(namespace)


@pytest.mark.parametrize(
    "param_func, is_json_params",
    [
        (json_params__column_names, True),
        (json_params__column_indices, True),
        (
            lambda: (
                f"column-names -i {EXAMPLE_CSV} -o output.tsv "
                "--force-comma --force-header-row-index 1 "
                "-c col1 col2 -C opt-col4 opt-col5 -c col3 "
                "--output-as-tsv "
                "-r col1=COL1 col3=COL3"
            ),
            False,
        ),
    ],
)
def test_CleanArgs__with_null_summary(param_func, is_json_params, make_json_cmd):
    # Given
    if is_json_params:
        json_params = param_func()
        json_params["summary_file"] = None
        cmd = make_json_cmd(json_params)
    else:
        cmd = param_func().split()
    expected = None

    # When
    argparser = _parser.get_argparser()
    namespace = argparser.parse_args(cmd)
    clean_args = _struct.CleanArgs.from_namespace(namespace)

    # Then
    assert clean_args.summary_file == expected


@pytest.mark.parametrize(
    "param_func, is_json_params",
    [
        (json_params__column_names, True),
        (json_params__column_indices, True),
        (
            lambda: (
                f"column-names {EXAMPLE_CSV} "
                "--force-comma --force-header-row-index 1 "
                "-C opt-col4 opt-col5"
                "-o output.tsv "
                "--output-as-tsv "
                "-s summary.json "
            ),
            False,
        ),
    ],
)
def test_CleanArgs__without_required_columns(param_func, is_json_params, make_json_cmd):
    # Given
    if is_json_params:
        json_params = param_func()
        json_params["required_columns"] = []
        json_params["reheader_mapping"] = []
        cmd = make_json_cmd(json_params)
        exc_type = ValidationError
    else:
        exc_type = SystemExit
        cmd = param_func().split()

    # When
    argparser = _parser.get_argparser()

    # Then
    with pytest.raises(exc_type):
        namespace = argparser.parse_args(cmd)
        _struct.CleanArgs.from_namespace(namespace)


@pytest.mark.parametrize(
    "param_func",
    [json_params__column_names, json_params__column_indices],
)
@pytest.mark.parametrize(
    "key_to_remove",
    [
        const.JSON_PARAM__MODE,
        const.JSON_PARAM__INPUT_FILE,
        const.JSON_PARAM__OUTPUT_FILE,
        const.JSON_PARAM__SUMMARY_FILE,
        const.JSON_PARAM__COLUMN_ORDER,
        const.JSON_PARAM__REQUIRED_COLUMNS,
        const.JSON_PARAM__OPTIONAL_COLUMNS,
        const.JSON_PARAM__REHEADER,
        const.JSON_PARAM__OUTPUT_DELIMITER,
        const.JSON_PARAM__FORCED_INPUT_DELIMITER,
        const.JSON_PARAM__FORCED_HEADER_ROW_INDEX,
    ],
)
def test_CleanArgs__will_raise_if_dict_missing_key(
    param_func, key_to_remove, make_json_cmd
):
    # Given
    json_params = param_func()
    json_params.pop(key_to_remove)
    cmd = make_json_cmd(json_params)

    # When
    argparser = _parser.get_argparser()
    namespace = argparser.parse_args(cmd)

    # Then
    with pytest.raises(ValidationError):
        _struct.CleanArgs.from_namespace(namespace)


@pytest.mark.parametrize(
    "cmd, should_throw",
    [
        pytest.param(
            f"column-names -i {EXAMPLE_CSV} -o out.csv -c col1 col2 -C opt-col4 opt-col5 -c col3 --output-as-tsv -r col1=COL1A col3=COL3",
            False,
            id="valid",
        ),
        pytest.param(
            f"column-names -i {EXAMPLE_CSV} -o out.csv -c col1 col2 -C opt-col4 opt-col5 -c col3 --output-as-tsv -r col1=COL1A col1=COL1B col3=COL3",
            True,
            id="invalid#dupes-in-input-headers",
        ),
        pytest.param(
            f"column-names -i {EXAMPLE_CSV} -o out.csv -c col1 col2 -C opt-col4 opt-col5 -c col3 --output-as-tsv -r col1=COL1 col2=COL1 col3=COL3",
            True,
            id="invalid#dupes-in-remapped-headers",
        ),
    ],
)
def test_CleanArgs__will_raise_if_reheader_has_dupliates(cmd, should_throw):
    # Given
    argparser = _parser.get_argparser()
    namespace = argparser.parse_args(cmd.split())

    # When
    if should_throw:
        # When & Then
        with pytest.raises(ValidationError):
            _struct.CleanArgs.from_namespace(namespace)
    else:
        # When
        clean_args = _struct.CleanArgs.from_namespace(namespace)

        # Then
        assert clean_args.reheader_mapping == {"col1": "COL1A", "col3": "COL3"}
