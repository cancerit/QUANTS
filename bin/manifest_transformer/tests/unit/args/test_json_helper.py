import typing as t
import pytest
from pathlib import Path
from collections import OrderedDict
import json

from src.exceptions import ValidationError
from src.args import _json_helper

# PARAMS
DUPLICATE_KEY_PARAMS = [
    pytest.param(
        [
            ("key1", "value1A"),
            ("key2", "value2A"),
            ("key3", "value3A"),
        ],
        False,
        id="no_duplicate_keys",
    ),
    pytest.param(
        [
            ("key1", "value1A"),
            ("key2", "value2A"),
            ("key2", "value2B"),
            ("key3", "value3A"),
        ],
        True,
        id="duplicate_keys",
    ),
    pytest.param([], False, id="empty_list"),
    pytest.param(
        [
            ("key1", "value1A"),
            ("key1", "value1A"),
        ],
        True,
        id="duplicate_keys_same_value",
    ),
    pytest.param([("key", "value")], False, id="single_key_value_pair"),
    pytest.param(
        [
            ("key1", "value1"),
            ("key2", "value2"),
            ("key2", "value2B"),
            ("key1", "value1B"),
        ],
        True,
        id="multiple_duplicate_keys",
    ),
    pytest.param(
        [
            (1, "value1A"),
            (1, "value1B"),
        ],
        True,
        id="non_string_duplicate_keys",
    ),
    pytest.param(
        [
            (1, "value1"),
            (2, "value2"),
        ],
        False,
        id="non_string_keys",
    ),
    pytest.param(
        [
            ("key1", None),
            ("key2", "value2"),
            ("key3", "value3"),
        ],
        False,
        id="keys_with_none_value",
    ),
    pytest.param(
        [
            ("Key", "value1"),
            ("key", "value2"),
        ],
        False,
        id="case_sensitive_keys",
    ),
]

# FIXTURES


@pytest.fixture
def make_json_file_from_str(
    tmp_path: Path,
) -> t.Generator[t.Callable[[str], Path], None, None]:
    import json

    json_file = tmp_path / "json_params.json"

    def _make_json_params(json_raw_data: str) -> Path:
        with open(json_file, "w") as f:
            f.write(json_raw_data)
        return json_file

    yield _make_json_params


# TESTS


@pytest.mark.parametrize(
    "key_value_pairs, should_raise",
    DUPLICATE_KEY_PARAMS,
)
def test_handle_duplicate_keys(key_value_pairs, should_raise):
    # Given: Some key-value pairs

    # When
    if should_raise:
        with pytest.raises(ValidationError):
            result = _json_helper.handle_duplicate_keys(key_value_pairs)
        return
    else:
        result = _json_helper.handle_duplicate_keys(key_value_pairs)
        expected_result = OrderedDict(key_value_pairs)

    assert result == expected_result


@pytest.mark.parametrize(
    "json_file_text, should_raise",
    [
        pytest.param(
            """
            {
                "key1": "value1",
                "key2": "value2",
                "key3": ["value3A", "value3B"],
                "key4": {"1": "value4A", "2": "value4B"},
                "key5": null
            }
            """,
            False,
            id="valid_json",
        ),
        pytest.param(
            """
            {
                "key1": "value1",
                "key2": "value2a",
                "key2": "value2b",
                "key3": ["value3A", "value3B"],
                "key4": {"1": "value4A", "2": "value4B"},
                "key5": null
            }
            """,
            True,
            id="duplicate_keys",
        ),
        pytest.param(
            """
            col1,col2,col3
            value1,value2,value3
            """,
            True,
            id="not_json",
        ),
    ],
)
def test_load_json_file(
    make_json_file_from_str: t.Callable[[str], Path],
    json_file_text: str,
    should_raise: bool,
):
    # Given: A json file with some text
    json_file = make_json_file_from_str(json_file_text)

    # When
    if should_raise:
        with pytest.raises(ValidationError):
            result = _json_helper.load_json_file(json_file)
        return
    else:
        result = _json_helper.load_json_file(json_file)
        expected_result = json.loads(json_file_text)

    assert result == expected_result
