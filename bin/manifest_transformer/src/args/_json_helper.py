import json as _json
import typing as t
from collections import OrderedDict

from src.exceptions import ValidationError

if t.TYPE_CHECKING:
    from pathlib import Path


def load_json_file(json_file: "Path") -> t.Dict[str, t.Any]:
    """
    Reads a JSON file and returns the contents as a dictionary.
    """
    with json_file.open("r") as handle:
        try:
            data = _json.load(handle, object_pairs_hook=handle_duplicate_keys)
        except _json.JSONDecodeError as e:
            msg = f"Invalid JSON file cannot be decoded: got {str(json_file)!r}, is it JSON?"
            raise ValidationError(msg) from e
    return data


def handle_duplicate_keys(
    key_value_pairs: t.List[t.Tuple[str, t.Any]]
) -> t.Dict[str, t.Any]:
    """
    Raises a ValidationError if the key_value_pairs has duplicate keys or
    """
    if _has_duplicate_keys(key_value_pairs):
        _throw_duplicate_keys(key_value_pairs)
    return OrderedDict(key_value_pairs)


def _has_duplicate_keys(key_value_pairs: t.List[t.Tuple[str, t.Any]]) -> bool:
    """
    Returns True if the key_value_pairs has duplicate keys, False otherwise.
    """
    seen = set()
    for key, _ in key_value_pairs:
        if key in seen:
            return True
        seen.add(key)
    return False


def _throw_duplicate_keys(key_value_pairs: t.List[t.Tuple[str, t.Any]]):
    """
    Raises a ValidationError with a message about duplicate keys in a JSON file.
    """
    human_readable_count = {1: "once", 2: "twice", 3: "thrice"}
    key_to_values = {}
    for key, value in key_value_pairs:
        key_to_values.setdefault(key, []).append(value)
    details = []
    for key, values in key_to_values.items():
        # Skip non-duplicate keys
        count = len(values)
        if count == 1:
            continue
        values_str = ", ".join(repr(value) for value in values)
        count_str = human_readable_count.get(count, f"{count} times")
        detail = f"found key {key!r} {count_str} (with values {values_str})"
        details.append(detail)
    details_str = "; ".join(details)

    msg = f"Invalid JSON file with duplicate keys in same JSON object: {details_str}."
    raise ValidationError(msg)
