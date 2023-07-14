import typing as t

from dataclasses import dataclass, field

from src import exceptions as exc
from src.enums import ColumnMode

if t.TYPE_CHECKING:
    from src.csv.parser import CSVParser
    from src.csv.properties import CSVFileProperties
    from src.args import CleanArgs


@dataclass
class CSVValidationReport:
    is_1_indexed: bool
    delimiter: str
    has_forced_delimiter: bool
    has_column_headers: bool
    has_forced_columns_headers: bool
    file_columns: t.Tuple[t.Union[str, int], ...]
    has_file_header: bool
    missing_required_columns: t.Tuple[t.Union[str, int], ...]
    missing_optional_columns: t.Tuple[t.Union[str, int], ...]
    number_of_columns: int
    is_columns_consistent: bool
    rows_with_nulls: t.Tuple[int, ...]
    _errors: t.List[str] = field(default_factory=list, init=True, hash=False)
    _warnings: t.List[str] = field(default_factory=list, init=True, hash=False)

    def get_errors(self) -> t.List[str]:
        return self._errors.copy()

    def get_warnings(self) -> t.List[str]:
        return self._warnings.copy()

    def is_valid(self) -> bool:
        self._errors = []
        self._warnings = []
        self._validate()
        return not self._errors

    def _validate(self):
        self._validate_required_columns()
        self._validate_optional_columns()
        self._validate_column_consistency()
        self._validate_nulls()

    def _validate_required_columns(self):
        if self.missing_required_columns:
            detail_missing = ", ".join(
                f"{str(elem)!r}" for elem in self.missing_required_columns
            )
            err_msg = f"Some required columns are missing: {detail_missing}."
            self._errors.append(err_msg)

    def _validate_optional_columns(self):
        if self.missing_optional_columns:
            detail_missing = ", ".join(
                f"{str(elem)!r}" for elem in self.missing_optional_columns
            )
            err_msg = f"Some optional columns are missing: {detail_missing}."
            self._warnings.append(err_msg)

    def _validate_column_consistency(self):
        if not self.is_columns_consistent:
            err_msg = (
                "The number of columns is inconsistent across the rows in the file."
            )
            self._errors.append(err_msg)

    def _validate_nulls(self):
        if self.rows_with_nulls:
            detail_rows = ", ".join(f"{str(elem)!r}" for elem in self.rows_with_nulls)
            err_msg = f"Some rows have null values: indices {detail_rows}."
            self._warnings.append(err_msg)

    def report(self) -> t.List[str]:
        null = "none"
        yes = "Yes"
        no = "No"
        seperator = " " * 1

        indexing = "1-indexed" if self.is_1_indexed else "0-indexed"
        file_delimiter = (
            f"{self.delimiter!r}{' (overridden)' if self.has_forced_delimiter else ''}"
        )
        has_column_headers = (
            f"{yes}"
            if self.has_column_headers
            else f"{no}"
            + f"{' (overridden)' if self.has_forced_columns_headers else ''}"
        )
        has_file_headers = f"{yes}" if self.has_file_header else f"{no}"
        file_header_columns = ", ".join(str(col) for col in self.file_columns)
        missing_required_cols = (
            ", ".join(str(col) for col in self.missing_required_columns)
            if self.missing_required_columns
            else null
        )
        missing_optional_cols = (
            ", ".join(str(col) for col in self.missing_optional_columns)
            if self.missing_optional_columns
            else null
        )
        column_consistency = (
            f"{yes} ({self.number_of_columns})"
            if self.is_columns_consistent
            else f"{no} (median size: {self.number_of_columns})"
        )
        rows_with_nulls = (
            ", ".join(str(row) for row in self.rows_with_nulls)
            if self.rows_with_nulls
            else null
        )

        lines = [
            "INPUT FILE REPORT",
            f"Indexing:{seperator}{indexing}",
            f"Which delimiter is used:{seperator}{file_delimiter}",
            f"Are header columns detected in file:{seperator}{has_column_headers}",
            f"Are file headers detected in file:{seperator}{has_file_headers}",
            f"File's actual column headers:{seperator}{file_header_columns}",
            f"Missing required columns:{seperator}{missing_required_cols}",
            f"Missing optional columns:{seperator}{missing_optional_cols}",
            f"Rows have constant column count:{seperator}{column_consistency}",
            f"Rows have null values:{seperator}{rows_with_nulls}",
        ]
        return lines


def get_validation_report(
    clean_args: "CleanArgs",
    csv_parser: "CSVParser",
    csv_file_properties: "CSVFileProperties",
) -> CSVValidationReport:
    CA_0_idx = clean_args.copy_as_0_indexed()
    CA_1_idx = clean_args.copy_as_1_indexed()
    # Find the detected column-headers detected and whether forced or not
    has_column_headers = csv_file_properties.has_column_headers()
    has_forced_columns_headers = (
        csv_file_properties.is_forced_column_headers_line_index()
    )

    # Find the detected file-header detected
    has_file_header = csv_file_properties.has_file_headers()

    # Get the columns from the CSV file, depending on the mode.
    file_columns = (
        csv_parser.column_header_names()
        if CA_0_idx.mode == ColumnMode.COLUMN_NAMES
        else csv_parser.column_indices(
            one_index=CA_1_idx.is_1_indexed,
            comprehensive=True,
        )
    )

    # Find the detected delimiter and whether it was forced or not
    which_delimiter = csv_file_properties.delimiter
    has_forced_delimiter = csv_file_properties.is_forced_delimiter()

    # Find any missing required columns
    missing_required_columns = find_missing_columns(
        user_columns=CA_1_idx.required_columns,
        file_columns=file_columns,
    )

    # Find any missing optional columns
    missing_optional_columns = find_missing_columns(
        user_columns=CA_1_idx.optional_columns,
        file_columns=file_columns,
    )

    # Find if the column dimensions are consistent across the file
    (
        number_of_columns,
        is_columns_consistent,
    ) = csv_parser.count_columns_comprehensively()

    # Find if any rows have null values
    rows_with_nulls = csv_parser.find_rows_with_nulls(one_index=CA_1_idx.is_1_indexed)

    # Generate the validation report
    validation_report = CSVValidationReport(
        is_1_indexed=CA_1_idx.is_1_indexed,
        delimiter=which_delimiter,
        has_forced_delimiter=has_forced_delimiter,
        has_column_headers=has_column_headers,
        has_forced_columns_headers=has_forced_columns_headers,
        file_columns=file_columns,
        has_file_header=has_file_header,
        missing_required_columns=tuple(missing_required_columns),
        missing_optional_columns=tuple(missing_optional_columns),
        number_of_columns=number_of_columns,
        is_columns_consistent=is_columns_consistent,
        rows_with_nulls=tuple(rows_with_nulls),
    )
    return validation_report


def assert_column_headers_detected(
    mode: ColumnMode,
    has_column_headers: bool,
    has_user_forced_column_header_index: bool,
):
    should_throw = ColumnMode.COLUMN_NAMES == mode and not has_column_headers
    needs_user_intervention = not has_user_forced_column_header_index
    if should_throw:
        mode_str = mode.value
        index_mode_str = ColumnMode.COLUMN_INDICES.value
        opt_detail = (
            f" (which is required while in {mode_str!r} mode)"
            if mode == ColumnMode.COLUMN_NAMES
            else ""
        )
        if needs_user_intervention:
            msg = (
                f"No column headers detected in file{opt_detail}. "
                "Please check the file has column headers, "
                "then force the column header index (see help) and try again. "
                f"If the file has no column headers, use {index_mode_str!r} mode instead."
            )
            raise exc.UserInterventionRequired(msg)
        else:
            msg = (
                f"No column headers detected in file{opt_detail} even with a forced column header index. "
                "Please check the file has column headers "
                f"or use {index_mode_str!r} mode instead."
            )
            raise exc.ValidationError(msg)
    return


def find_missing_columns(
    user_columns: t.Sequence[t.Any], file_columns: t.Sequence[t.Any]
) -> t.List[t.Any]:
    """
    Find any missing columns in the file, compared to the user's column list.
    """
    user_columns_set = set(user_columns)
    file_columns_set = set(file_columns)

    missing_columns_not_found_in_file = user_columns_set - file_columns_set
    return sorted(missing_columns_not_found_in_file)

    # Find if the column dimensions are consistent across the file

    # Find if any rows have missing values

    # Find whether the file had file-headers detected or not

    # Find whether the file had column-headers detected or not
