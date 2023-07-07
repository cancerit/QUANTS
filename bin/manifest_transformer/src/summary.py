import typing as t
import sys

import json
from collections import OrderedDict

from src.version import VERSION
from src.args import _json_helper


if t.TYPE_CHECKING:
    from pathlib import Path


def get_full_command() -> str:
    """
    Returns the full command used to invoke the script at runtime.
    """
    return " ".join(sys.argv)


def get_summary(
    input_file: "Path", output_file: "Path", maybe_json_params_file: "Path"
) -> t.Dict[str, t.Any]:
    """
    Writes the summary to the summary file.
    """
    summary = OrderedDict()
    summary["version"] = VERSION
    summary["command"] = get_full_command()
    summary["input_file"] = str(input_file.absolute())
    summary["output_file"] = str(output_file.absolute())

    if maybe_json_params_file.suffix == ".json":
        params = _json_helper.read_json_file(maybe_json_params_file)
        summary["params"] = params
    else:
        summary["params"] = None

    return summary


def write_summary(
    summary_file: "Path",
    input_file: "Path",
    output_file: "Path",
    maybe_json_params_file: "Path",
) -> None:
    summary = get_summary(
        input_file=input_file,
        output_file=output_file,
        maybe_json_params_file=maybe_json_params_file,
    )
    summary_file.write_text(json.dumps(summary, indent=4))
    return
