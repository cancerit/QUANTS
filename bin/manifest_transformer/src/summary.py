import typing as t
import sys
import datetime

import json
from collections import OrderedDict

from src.version import VERSION
from src.args import _json_helper
from src import constants as const


if t.TYPE_CHECKING:
    from pathlib import Path


def get_full_command() -> str:
    """
    Returns the full command used to invoke the script at runtime.
    """
    return " ".join(sys.argv)


def get_summary(
    input_file: "Path", output_file: "Path", maybe_json_params_file: t.Optional["Path"]
) -> t.Dict[str, t.Optional[t.Union[str, t.Dict[str, t.Any]]]]:
    """
    Writes the summary to the summary file.
    """
    summary: t.Dict[str, t.Optional[t.Union[str, t.Dict[str, t.Any]]]] = OrderedDict()
    summary[const.JSON_SUMMARY__VERSION] = VERSION
    summary[const.JSON_SUMMARY__COMMAND] = get_full_command()
    summary[const.JSON_SUMMARY__INPUT_FILE] = str(input_file.absolute())
    summary[const.JSON_SUMMARY__OUTPUT_FILE] = str(output_file.absolute())
    summary[const.JSON_SUMMARY__TIMESTAMP] = _get_current_timestamp_string()

    if maybe_json_params_file is not None:
        params = _json_helper.read_json_file(maybe_json_params_file)
        summary[const.JSON_SUMMARY__JSON_PARAMS_FILE] = str(maybe_json_params_file)
        summary[const.JSON_SUMMARY__JSON_PARAMS] = params
    else:
        summary[const.JSON_SUMMARY__JSON_PARAMS_FILE] = None
        summary[const.JSON_SUMMARY__JSON_PARAMS] = None

    return summary


def write_summary(
    summary_file: "Path",
    input_file: "Path",
    output_file: "Path",
    maybe_json_params_file: t.Optional["Path"],
) -> None:
    summary = get_summary(
        input_file=input_file,
        output_file=output_file,
        maybe_json_params_file=maybe_json_params_file,
    )
    summary_file.write_text(json.dumps(summary, indent=4))
    return


def _get_current_timestamp_string() -> str:
    now = datetime.datetime.now()
    now_tz_aware = now.astimezone()
    iso_datetime_str = now_tz_aware.isoformat()
    return iso_datetime_str
