import json as _json
import typing as t

if t.TYPE_CHECKING:
    from pathlib import Path


def read_json_file(json_file: "Path") -> t.Dict[str, t.Any]:
    """
    Reads a JSON file and returns the contents as a dictionary.
    """
    with json_file.open("r") as handle:
        data = _json.load(handle)
    return data
