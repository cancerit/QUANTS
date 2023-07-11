import typing as t
import io
import csv

from src.args import CleanArgs
from src.csv.parser import CSVParser, get_column_order_as_indices
from src.csv.properties import CSVFileProperties
from src.csv._transform import ReorderColumns


def create_transfored_rows(
    csv_parser: CSVParser, column_order: t.Iterable[int]
) -> t.List[t.List[t.Any]]:
    result = []

    reorder_row = ReorderColumns(column_order).reorder

    with csv_parser.get_csv_reader() as csv_reader:
        for row in csv_reader:
            transformed_row = reorder_row(row)
            result.append(transformed_row)
    return result


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
    transformed_rows = create_transfored_rows(
        csv_parser=csv_parser,
        column_order=column_order,
    )

    # Write the transformed CSV file.
    output_file = io.StringIO()
    csv_writer = csv.writer(output_file, delimiter=CA.output_file_delimiter)
    csv_writer.writerows(transformed_rows)
    output_file.seek(0)
    return output_file
