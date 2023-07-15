import typing as t
from pathlib import Path
import csv

from src import constants as const


def write_rows(
    dict_rows: t.Iterator[t.Dict[str, str]], headers: t.List[str], output_file: Path
) -> None:
    """
    Write rows to output file.
    """
    with open(output_file, "w") as output:
        csv_writer = csv.DictWriter(
            output, fieldnames=headers, delimiter=const._OUTPUT_DELIMITER
        )
        csv_writer.writeheader()
        csv_writer.writerows(dict_rows)
