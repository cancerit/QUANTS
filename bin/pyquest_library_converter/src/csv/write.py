import typing as t
from pathlib import Path
import csv
import sys

from src import constants as const


def write_rows(
    dict_rows: t.Iterator[t.Dict[str, str]], headers: t.List[str], output_file: Path
) -> None:
    """
    Write rows to output file.
    """
    command = get_full_command()
    command_comment = f"## {command}\n"
    with open(output_file, "w") as output:
        output.write(command_comment)
        csv_writer = csv.DictWriter(
            output, fieldnames=headers, delimiter=const._OUTPUT_DELIMITER
        )
        csv_writer.writeheader()
        csv_writer.writerows(dict_rows)


def get_full_command() -> str:
    """
    Returns the full command used to invoke the script at runtime.
    """
    return " ".join(sys.argv)
