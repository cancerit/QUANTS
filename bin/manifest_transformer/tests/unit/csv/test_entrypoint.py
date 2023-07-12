import typing as t
import csv
from pathlib import Path

import pytest

from src.csv import _entrypoint
from src import constants as const
from src.args import get_argparser, CleanArgs
from tests.conftest import json_params__column_names, json_params__column_indices
from src.exceptions import ValidationError


# CONSTANTS
REQ_COL_KEY = const.JSON_PARAM__REQUIRED_COLUMNS
OPT_COL_KEY = const.JSON_PARAM__OPTIONAL_COLUMNS
COL_ORDER_KEY = const.JSON_PARAM__COLUMN_ORDER


# PARAMS

PARAMS_HAS_COLUMN_HEADER = [
    pytest.param(True, id="has_column_header"),
    pytest.param(False, id="no_column_header"),
]
PARAMS_HAS_FILE_HEADER = [
    pytest.param(True, id="has_file_header"),
    pytest.param(False, id="no_file_header"),
]
PARAMS_INPUT_FILE_DELIMETER = [
    pytest.param(",", id="forced_input_delimiter_comma"),
    pytest.param("\t", id="forced_input_delimiter_tab"),
    pytest.param(None, id="no_forced_input_delimiter"),
]
PARAMS_OUTPUT_FILE_DELIMETER = [
    pytest.param(",", id="output_delimiter_comma"),
    pytest.param("\t", id="output_delimiter_tab"),
]
PARAMS_COLUMN_MODE_AND_COLUMNS = [
    # COLUMN NAMES
    pytest.param(
        const.SUBCOMMAND__COLUMN_NAMES,
        {
            REQ_COL_KEY: ["col_0", "col_1", "col_2", "col_3", "col_4"],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: ["col_0", "col_1", "col_2", "col_3", "col_4"],
        },
        False,
        {
            "col_0": "COL_0",
            "col_1": "COL_1",
            "col_2": "COL_2",
            "col_3": "COL_3",
            "col_4": "COL_4",
        },
        id="column_names+all_required+no_optional+in_order+append=False+all_reheader_cols",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_NAMES,
        {
            REQ_COL_KEY: ["col_0", "col_1", "col_2", "col_3", "col_4"],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: ["col_3", "col_4", "col_0", "col_2", "col_1"],
        },
        False,
        {
            "col_0": "COL_0",
            "col_1": "COL_1",
            "col_2": "COL_2",
            "col_3": "COL_3",
            "col_4": "COL_4",
        },
        id="column_names+all_required+no_optional+random_order+append=False+all_reheader_cols",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_NAMES,
        {
            REQ_COL_KEY: ["col_0", "col_1", "col_2", "col_3", "col_4"],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: ["col_0", "col_1", "col_2", "col_3", "col_4"],
        },
        False,
        {"col_0": "COL_0", "col_1": "COL_1", "col_2": "COL_2"},
        id="column_names+all_required+no_optional+in_order+append=False+partial_reheader_cols",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_NAMES,
        {
            REQ_COL_KEY: ["col_0", "col_1", "col_2", "col_3", "col_4"],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: ["col_3", "col_4", "col_0", "col_2", "col_1"],
        },
        False,
        {"col_0": "COL_0", "col_1": "COL_1", "col_2": "COL_2"},
        id="column_names+all_required+no_optional+random_order+append=False+partial_reheader_cols",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_NAMES,
        {
            REQ_COL_KEY: ["col_0", "col_1", "col_2"],
            OPT_COL_KEY: ["col_3", "col_4"],
            COL_ORDER_KEY: ["col_0", "col_1", "col_2", "col_3", "col_4"],
        },
        False,
        {"col_0": "COL_0", "col_1": "COL_1", "col_2": "COL_2"},
        id="column_names+3_required+2_optional+in_order+append=False+partial_reheader_cols",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_NAMES,
        {
            REQ_COL_KEY: ["col_0", "col_1", "col_2"],
            OPT_COL_KEY: ["col_3", "col_4"],
            COL_ORDER_KEY: ["col_3", "col_4", "col_0", "col_2", "col_1"],
        },
        False,
        {"col_0": "COL_0", "col_1": "COL_1", "col_2": "COL_2"},
        id="column_names+3_required+2_optional+random_order+append=False+partial_reheader_cols",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_NAMES,
        {
            REQ_COL_KEY: ["col_0"],
            OPT_COL_KEY: ["col_4"],
            COL_ORDER_KEY: ["col_0", "col_4"],
        },
        False,
        {"col_0": "COL_0", "col_4": "COL_4"},
        id="column_names+1_required+1_optional+in_order+append=False+complete_reheader_cols",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_NAMES,
        {
            REQ_COL_KEY: ["col_0"],
            OPT_COL_KEY: ["col_4"],
            COL_ORDER_KEY: ["col_4", "col_0"],
        },
        False,
        {"col_0": "COL_0", "col_4": "COL_4"},
        id="column_names+1_required+1_optional+random_order+append=False+complete_reheader_cols",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_NAMES,
        {
            REQ_COL_KEY: ["col_0"],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: ["col_0"],
        },
        False,
        {"col_0": "COL_0"},
        id="column_names+1_required+no_optional+in_order+append=False+complete_reheader_cols",
    ),
    # COLUMN INDICES
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1, 2, 3, 4, 5],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: [1, 2, 3, 4, 5],
        },
        True,
        {1: "COL_0", 2: "COL_1", 3: "COL_2", 4: "COL_3", 5: "COL_4"},
        id="column_indices+all_required+no_optional+in_order+append=True",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1, 2, 3, 4, 5],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: [1, 2, 3, 4, 5],
        },
        False,
        {1: "COL_0", 2: "COL_1", 3: "COL_2", 4: "COL_3", 5: "COL_4"},
        id="column_indices+all_required+no_optional+in_order+append=False",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1, 2, 3, 4, 5],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: [4, 5, 1, 3, 2],
        },
        True,
        {1: "COL_0", 2: "COL_1", 3: "COL_2", 4: "COL_3", 5: "COL_4"},
        id="column_indices+all_required+no_optional+random_order+append=True",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1, 2, 3, 4, 5],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: [4, 5, 1, 3, 2],
        },
        False,
        {1: "COL_0", 2: "COL_1", 3: "COL_2", 4: "COL_3", 5: "COL_4"},
        id="column_indices+all_required+no_optional+random_order+append=False",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1, 2, 3],
            OPT_COL_KEY: [4, 5],
            COL_ORDER_KEY: [1, 2, 3, 4, 5],
        },
        True,
        {1: "COL_0", 2: "COL_1", 3: "COL_2", 4: "COL_3", 5: "COL_4"},
        id="column_indices+3_required+2_optional+in_order+append=True",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1, 2, 3],
            OPT_COL_KEY: [4, 5],
            COL_ORDER_KEY: [1, 2, 3, 4, 5],
        },
        False,
        {1: "COL_0", 2: "COL_1", 3: "COL_2", 4: "COL_3", 5: "COL_4"},
        id="column_indices+3_required+2_optional+in_order+append=False",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1, 2, 3],
            OPT_COL_KEY: [4, 5],
            COL_ORDER_KEY: [4, 5, 1, 3, 2],
        },
        True,
        {1: "COL_0", 2: "COL_1", 3: "COL_2", 4: "COL_3", 5: "COL_4"},
        id="column_indices+3_required+2_optional+random_order+append=True",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1, 2, 3],
            OPT_COL_KEY: [4, 5],
            COL_ORDER_KEY: [4, 5, 1, 3, 2],
        },
        False,
        {1: "COL_0", 2: "COL_1", 3: "COL_2", 4: "COL_3", 5: "COL_4"},
        id="column_indices+3_required+2_optional+random_order+append=False",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1],
            OPT_COL_KEY: [5],
            COL_ORDER_KEY: [1, 5],
        },
        True,
        {1: "COL_0", 5: "COL_4"},
        id="column_indices+1_required+1_optional+in_order+append=True",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1],
            OPT_COL_KEY: [5],
            COL_ORDER_KEY: [1, 5],
        },
        False,
        {1: "COL_0", 5: "COL_4"},
        id="column_indices+1_required+1_optional+in_order+append=False",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1],
            OPT_COL_KEY: [5],
            COL_ORDER_KEY: [5, 1],
        },
        True,
        {1: "COL_0", 5: "COL_4"},
        id="column_indices+1_required+1_optional+random_order+append=True",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1],
            OPT_COL_KEY: [5],
            COL_ORDER_KEY: [5, 1],
        },
        False,
        {1: "COL_0", 5: "COL_4"},
        id="column_indices+1_required+1_optional+random_order+append=False",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: [1],
        },
        True,
        {1: "COL_0"},
        id="column_indices+1_required+no_optional+in_order+append=True",
    ),
    pytest.param(
        const.SUBCOMMAND__COLUMN_INDICES,
        {
            REQ_COL_KEY: [1],
            OPT_COL_KEY: [],
            COL_ORDER_KEY: [1],
        },
        False,
        {1: "COL_0"},
        id="column_indices+1_required+no_optional+in_order+append=False",
    ),
]

# TEST


@pytest.mark.parametrize(
    "has_file_header",
    PARAMS_HAS_FILE_HEADER,
)
@pytest.mark.parametrize(
    "has_column_header",
    PARAMS_HAS_COLUMN_HEADER,
)
@pytest.mark.parametrize(
    "input_delimiter",
    PARAMS_INPUT_FILE_DELIMETER,
)
@pytest.mark.parametrize(
    "output_delimiter",
    PARAMS_OUTPUT_FILE_DELIMETER,
)
@pytest.mark.parametrize(
    "column_mode, columns, should_append_reheader, reheader_mapping",
    PARAMS_COLUMN_MODE_AND_COLUMNS,
)
def test_manifest_transformer(
    # Parametrized arguments
    has_file_header: bool,
    has_column_header: bool,
    input_delimiter: t.Optional[str],
    output_delimiter: str,
    column_mode: str,
    columns: t.Dict[str, t.Any],
    should_append_reheader: bool,
    reheader_mapping: t.Dict[t.Union[str, int], str],
    # Fixtures
    make_csv_file: t.Callable[[bool, int, bool, bool, bool, t.Optional[str]], "Path"],
    make_json_cmd: t.Callable[[t.Dict[str, t.Any]], t.List[str]],
):
    # Base setup - Prepare the CSV file
    csv_file = make_csv_file(
        is_erroneous=False,
        columns=5,
        delimiter=input_delimiter,
        include_file_header=has_file_header,
        include_column_header=has_column_header,
        include_null_values=False,
        null_value=None,
    )

    # Base setup - Prepare the JSON input file
    if column_mode == const.SUBCOMMAND__COLUMN_NAMES:
        json_params = json_params__column_names()
    elif column_mode == const.SUBCOMMAND__COLUMN_INDICES:
        json_params = json_params__column_indices()
    else:
        raise ValueError(f"Invalid column mode: {column_mode}")
    json_params[const.JSON_PARAM__MODE] = column_mode
    json_params[COL_ORDER_KEY] = columns[COL_ORDER_KEY]
    json_params[REQ_COL_KEY] = columns[REQ_COL_KEY]
    json_params[OPT_COL_KEY] = columns[OPT_COL_KEY]
    json_params[const.JSON_PARAM__REHEADER_APPEND] = should_append_reheader
    json_params[const.JSON_PARAM__REHEADER] = reheader_mapping
    json_params[const.JSON_PARAM__INPUT_FILE] = str(csv_file)
    json_params[const.JSON_PARAM__FORCED_INPUT_DELIMITER] = input_delimiter
    json_params[const.JSON_PARAM__OUTPUT_FILE] = None
    json_params[const.JSON_PARAM__OUTPUT_DELIMITER] = output_delimiter

    # Expected values
    should_throw = (
        column_mode == const.SUBCOMMAND__COLUMN_NAMES and not has_column_header
    )
    expected_rows_count = 10 + has_column_header

    # Given
    cmd = make_json_cmd(json_params)
    namespace = get_argparser().parse_args(cmd)
    clean_args = CleanArgs.from_namespace(namespace)

    # When
    if should_throw:
        with pytest.raises(ValidationError):
            _entrypoint.manifest_transformer(clean_args)
        return
    else:
        io_object = _entrypoint.manifest_transformer(clean_args)
        assert io_object is not None

    # Then
    csvreader = csv.reader(io_object, delimiter=output_delimiter)
    rows = list(csvreader)
    assert len(rows) == expected_rows_count, capture_bad_files(csv_file, json_params)


def capture_bad_files(csv_file, json_params):
    import json

    parent = Path("tests/failing_data_inputs")
    parent.mkdir(exist_ok=True)
    stem = csv_file.parent.name + "." + csv_file.stem
    new_csv_file = parent / f"{stem}.csv"
    new_csv_file.write_text(csv_file.read_text())

    new_json_file = parent / f"{stem}.json"
    new_json_file.write_text(json.dumps(json_params, indent=4))
    print(
        "\n\nThe failing files have been written to the following location: \n"
        f"- {str(new_csv_file)!r}\n- {str(new_json_file)!r}\n\n"
    )
    return
