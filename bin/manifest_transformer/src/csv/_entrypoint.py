import typing as t
import io
import csv
from functools import partial

from src.args import CleanArgs
from src.csv.parser import CSVParser, get_column_order_as_indices
from src.csv.properties import CSVFileProperties
from src.csv._transform import reorder_rows, ReheaderColumns
from src.csv import _validate
from src import cli
from src import exceptions


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
    """
    Trim, reorder and reheader a manifest file.
    """
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
    reheader_rows = ReheaderColumns(
        CA.reheader_mapping, mode=CA.mode.value, append=CA.reheader_append
    ).reheader_rows
    with csv_parser.get_csv_reader() as csv_reader:
        rows = iter(csv_reader)
        transformed_rows = process_rows(
            rows,
            reorder_func=partial_reorder_rows,
            reheader_func=reheader_rows,
        )
        transformed_rows = list(transformed_rows)

    # Write the transformed CSV file.
    output_file = io.StringIO()
    csv_writer = csv.writer(output_file, delimiter=CA.output_file_delimiter)
    csv_writer.writerows(transformed_rows)
    output_file.seek(0)
    return output_file


def manifest_validator(clean_args: CleanArgs) -> bool:
    """
    Returns True if the CSV file is valid, False otherwise.

    This function will log info and warnings to the console and throw an
    exception if the CSV file is invalid.

    """
    # Ensure clean_args are 0-indexed.
    CA_0_idx = clean_args.copy_as_0_indexed()

    # Prepare the CSV parser & properties.
    csv_file_properties = CSVFileProperties.from_clean_args(CA_0_idx)
    csv_parser = CSVParser.from_csv_file_properties(
        file_path=clean_args.input_file,
        csv_file_properties=csv_file_properties,
    )

    # Possibly abort early if in column name but the parser didn't detect any headers
    _validate.assert_column_headers_detected(
        mode=CA_0_idx.mode,
        has_column_headers=csv_file_properties.has_column_headers(),
        has_user_forced_column_header_index=csv_file_properties.is_forced_column_headers_line_index(),
    )

    # Get the validation report.
    validation_report = _validate.get_validation_report(
        clean_args=CA_0_idx,
        csv_parser=csv_parser,
        csv_file_properties=csv_file_properties,
    )
    is_valid = validation_report.is_valid()

    # Display the validation report.
    report = validation_report.report()
    for report_line in report:
        cli.display_info(report_line)
    for warning in validation_report.get_warnings():
        cli.display_warning(warning)
    if not is_valid:
        error_msg = validation_report.get_error_msg()
        raise exceptions.ValidationError(error_msg)
    return is_valid
