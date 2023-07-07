import typing as t
from pathlib import Path
from dataclasses import dataclass
import copy

from src.enums import ColumnMode
from src import constants as const
from src.args import _parser
from src.args import _clean

if t.TYPE_CHECKING:
    from argparse import Namespace


@dataclass
class CleanArgs:
    is_1_indexed: bool
    mode: ColumnMode
    input_file: Path
    output_file: Path
    summary_file: Path
    column_order: t.Tuple[t.Union[str, int], ...]
    required_columns: t.Tuple[t.Union[str, int], ...]
    optional_columns: t.Tuple[t.Union[str, int], ...]
    output_file_delimiter: str
    forced_intput_file_delimiter: t.Optional[str]
    forced_header_row_index: t.Optional[int]
    reheader_mapping: t.Dict[t.Union[str, int], str]

    def copy_as_0_indexed(self) -> "CleanArgs":
        """
        Return a copy of self with all column indices converted to 0-indexed

        This method is idempotent, meaning that if self is already 0-indexed,
        it will return a copy without any changes.
        """
        copy_args = copy.deepcopy(self)
        # If already 0-indexed, do nothing other than set is_1_indexed to False
        # Otherwise, convert all column indices to 0-indexed
        if self.is_1_indexed and self.mode == ColumnMode.COLUMN_INDICES:
            func = self._1_to_0_indexed
            copy_args.column_order = tuple(func(c) for c in self.column_order)
            copy_args.required_columns = tuple(func(c) for c in self.required_columns)
            copy_args.optional_columns = tuple(func(c) for c in self.optional_columns)
            copy_args.reheader_mapping = {
                func(k): v for k, v in self.reheader_mapping.items()
            }
            copy_args.forced_header_row_index = func(self.forced_header_row_index)
        copy_args.is_1_indexed = False
        return copy_args

    def copy_as_1_indexed(self) -> "CleanArgs":
        """
        Return a copy of self with all column indices converted to 1-indexed

        This method is idempotent, meaning that if self is already 1-indexed,
        it will return a copy without any changes.
        """
        copy_args = copy.deepcopy(self)
        # If already 1-indexed, do nothing other than set is_1_indexed to True
        # Otherwise, convert all column indices to 1-indexed
        if not self.is_1_indexed and self.mode == ColumnMode.COLUMN_INDICES:
            func = self._0_to_1_indexed
            copy_args.column_order = tuple(func(c) for c in self.column_order)
            copy_args.required_columns = tuple(func(c) for c in self.required_columns)
            copy_args.optional_columns = tuple(func(c) for c in self.optional_columns)
            copy_args.reheader_mapping = {
                func(k): v for k, v in self.reheader_mapping.items()
            }
            copy_args.forced_header_row_index = func(self.forced_header_row_index)
        copy_args.is_1_indexed = True
        return copy_args

    @staticmethod
    def _1_to_0_indexed(column: t.Union[t.Any, int]) -> t.Union[t.Any, int]:
        if isinstance(column, int):
            return column - 1
        return column

    @staticmethod
    def _0_to_1_indexed(column: t.Union[t.Any, int]) -> t.Union[t.Any, int]:
        if isinstance(column, int):
            return column + 1
        return column

    @staticmethod
    def _parse_and_clean_column_tuple(
        column_tuple: t.Tuple[str, ...], is_1_indexed: bool
    ) -> t.Tuple[int, ...]:
        parsed_columns = _parser.parse_integer_like_list(list(column_tuple))
        clean_columns = [
            _clean.strict_clean_index(c, is_1_indexed) for c in parsed_columns
        ]
        return tuple(clean_columns)

    @staticmethod
    def _parse_and_clean_column_dict(
        column_dict: t.Dict[str, str], is_1_indexed: bool
    ) -> t.Dict[int, str]:
        parsed_columns = _parser.parse_integer_like_dict(column_dict)
        clean_columns = {
            _clean.strict_clean_index(k, is_1_indexed): v
            for k, v in parsed_columns.items()
        }
        return clean_columns

    @classmethod
    def from_namespace(cls, namespace: "Namespace") -> "CleanArgs":
        is_1_indexed = True

        # Get raw values from namespace
        mode__raw = getattr(namespace, const.ARG_SUBCOMMAND)
        input_file__raw = getattr(namespace, const.ARG_INPUT)
        output_file__raw = getattr(namespace, const.ARG_OUTPUT)
        summary_file__raw = getattr(namespace, const.ARG_SUMMARY)
        parsed_columns = _parser.ParsedColumns.from_labelled_columns(
            getattr(namespace, const.ARG_COLUMNS)
        )
        output_file_delimiter__raw = (
            const.DELIMITER__TAB
            if getattr(namespace, const.ARG_CAST_OUTPUT_AS_TSV)
            else const.DELIMITER__COMMA
        )
        forced_intput_file_delimiter__raw = getattr(
            namespace, const.ARG_FORCE_DELIMITER
        )
        forced_header_row_index__raw = getattr(
            namespace, const.ARG_FORCE_HEADER_ROW_INDEX
        )
        reheader_mapping__raw = getattr(namespace, const.ARG_REHEADER)

        # Clean raw values
        mode = ColumnMode(mode__raw)
        input_file__clean = _clean.InputFile(input_file__raw).clean
        output_file__clean = _clean.OutputFile(input_file__raw, output_file__raw).clean
        summary_file__clean = _clean.SummaryFile(
            input_file__raw, summary_file__raw
        ).clean
        parsed_columns.assert_valid()
        column_order__raw = parsed_columns.column_order
        required_columns__raw = parsed_columns.required_columns
        optional_columns__raw = parsed_columns.optional_columns
        output_file_delimiter__clean = _clean.clean_output_delimiter(
            output_file_delimiter__raw
        )
        forced_intput_file_delimiter__clean = _clean.clean_input_delimiter(
            forced_intput_file_delimiter__raw
        )
        forced_header_row_index__clean = _clean.clean_index(
            forced_header_row_index__raw
        )
        reheader_mapping__raw = _parser.parse_reheader_columns(reheader_mapping__raw)

        # Normalize string columns to int columns, if necessary
        if mode == ColumnMode.COLUMN_INDICES:
            column_order__clean = cls._parse_and_clean_column_tuple(
                column_order__raw, is_1_indexed
            )
            required_columns__clean = cls._parse_and_clean_column_tuple(
                required_columns__raw, is_1_indexed
            )
            optional_columns__clean = cls._parse_and_clean_column_tuple(
                optional_columns__raw, is_1_indexed
            )
            reheader_mapping__clean = cls._parse_and_clean_column_dict(
                reheader_mapping__raw, is_1_indexed
            )
        else:
            column_order__clean = column_order__raw
            required_columns__clean = required_columns__raw
            optional_columns__clean = optional_columns__raw
            reheader_mapping__clean = reheader_mapping__raw

        # Create instance
        instance = cls(
            is_1_indexed=True,
            mode=mode,
            input_file=input_file__clean,
            output_file=output_file__clean,
            summary_file=summary_file__clean,
            column_order=column_order__clean,
            required_columns=required_columns__clean,
            optional_columns=optional_columns__clean,
            output_file_delimiter=output_file_delimiter__clean,
            forced_intput_file_delimiter=forced_intput_file_delimiter__clean,
            forced_header_row_index=forced_header_row_index__clean,
            reheader_mapping=reheader_mapping__clean,
        )
        return instance
