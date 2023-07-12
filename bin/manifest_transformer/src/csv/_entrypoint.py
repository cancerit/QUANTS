import typing as t
import io
import csv
from functools import partial

from src.args import CleanArgs
from src.csv.parser import CSVParser, get_column_order_as_indices
from src.csv.properties import CSVFileProperties
from src.csv._transform import reorder_rows


def process_rows(
    rows: t.Iterator[t.List[t.Any]],
    reorder_func: t.Callable[[t.Iterator[t.List[t.Any]]], t.Iterator[t.List[t.Any]]],
    reheader_func: t.Callable[[t.Iterator[t.List[t.Any]]], t.Iterator[t.List[t.Any]]],
) -> t.Iterable[t.List[t.Any]]:
    # We need to process the rows in a specific order:
    # 1. Reheader the rows first (otherwise the reheader mapping will be wrong).
    # 2. Reorder the rows second
    processed_rows = reheader_func(rows)
    processed_rows = reorder_func(processed_rows)
    return processed_rows


def manifest_transformer(clean_args: CleanArgs) -> io.StringIO:
    # Ensure clean_args are 0-indexed.
    CA = clean_args.copy_as_0_indexed()

    # Prepare the CSV parser.
    csv_file_properties = CSVFileProperties.from_clean_args(clean_args)
    csv_parser = CSVParser.from_csv_file_properties(
        file_path=clean_args.input_file,
        csv_file_properties=csv_file_properties,
    )

    # Prepare the column order.
    column_order = get_column_order_as_indices(
        mode=CA.mode,
        column_order=CA.column_order,
        csv_parser=csv_parser,
    )

    # Transform the CSV file.
    partial_reorder_rows = partial(reorder_rows, column_index_order=column_order)
    partial_reheader_rows = lambda rows: rows  # noqa:E731 TODO implement reheader_rows
    with csv_parser.get_csv_reader() as csv_reader:
        rows = iter(csv_reader)
        transformed_rows = process_rows(
            rows,
            reorder_func=partial_reorder_rows,
            reheader_func=partial_reheader_rows,
        )
        transformed_rows = list(transformed_rows)

    # Write the transformed CSV file.
    output_file = io.StringIO()
    csv_writer = csv.writer(output_file, delimiter=CA.output_file_delimiter)
    csv_writer.writerows(transformed_rows)
    output_file.seek(0)
    return output_file
