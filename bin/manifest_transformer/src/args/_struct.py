import typing as t
from pathlib import Path
from dataclasses import dataclass
import copy

from src.enums import ColumnMode
from src import constants as const
from src import exceptions as exc
from src.args import _parser
from src.args import _clean
from src.args import _json_helper

if t.TYPE_CHECKING:
    from argparse import Namespace


@dataclass
class CleanArgs:
    is_1_indexed: bool
    mode: ColumnMode
    input_file: Path
    output_file: Path
    summary_file: t.Optional[Path]
    column_order: t.Tuple[t.Union[str, int], ...]
    required_columns: t.Tuple[t.Union[str, int], ...]
    optional_columns: t.Tuple[t.Union[str, int], ...]
    output_file_delimiter: str
    forced_input_file_delimiter: t.Optional[str]
    forced_header_row_index: t.Optional[int]
    reheader_mapping: t.Dict[t.Union[str, int], str]
    reheader_append: bool
    _json_params_file: t.Optional[Path] = None

    @property
    def json_params_file(self) -> t.Optional[Path]:
        return self._json_params_file

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

    @staticmethod
    def _normalise_non_json_namespace_derived_dict(
        raw_dict: t.Dict[str, t.Any]
    ) -> t.Dict[str, t.Any]:
        """
        Normalise the namespace-derived dict to be more consistent with the JSON-derived dict
        """
        # HANDLE COLUMNS
        original_col_key = const.ARG_COLUMNS
        if original_col_key not in raw_dict:
            raise ValueError(
                f"Expected key {original_col_key!r} in namespace-derived dict"
            )
        # Namespace columns are labelled with "REQUIRED_COLUMN:" or "OPTIONAL_COLUMN:"
        # The columns need to processed and split into column order, required, and optional columns and then
        # added back to the dict while also removing the original key
        orginal_namespace_columns = raw_dict.pop(original_col_key)
        parsed_columns = _parser.ParsedColumns.from_labelled_columns(
            orginal_namespace_columns
        )

        raw_dict[const.JSON_PARAM__COLUMN_ORDER] = parsed_columns.column_order
        raw_dict[const.JSON_PARAM__REQUIRED_COLUMNS] = parsed_columns.required_columns
        raw_dict[const.JSON_PARAM__OPTIONAL_COLUMNS] = parsed_columns.optional_columns

        # HANDLE REHEADER
        reheader_key = const.ARG_REHEADER
        if reheader_key not in raw_dict:
            raise ValueError(f"Expected key {reheader_key!r} in namespace-derived dict")
        raw_reheader = raw_dict[reheader_key]
        parsed_reheader = _parser.parse_reheader_columns(raw_reheader)
        raw_dict[reheader_key] = parsed_reheader

        return raw_dict

    @classmethod
    def from_namespace(cls, namespace: "Namespace") -> "CleanArgs":
        allowed_subcommands = {
            const.SUBCOMMAND__COLUMN_INDICES,
            const.SUBCOMMAND__COLUMN_NAMES,
            const.SUBCOMMAND__JSON,
        }
        non_json_subcommands = allowed_subcommands - {const.SUBCOMMAND__JSON}
        subcommand = getattr(namespace, const.ARG_SUBCOMMAND)

        if subcommand == const.SUBCOMMAND__JSON:
            json_param_file__raw = getattr(namespace, const.ARG_INPUT)
            json_param_file__clean = _clean.InputFile(json_param_file__raw).clean
        elif subcommand in non_json_subcommands:
            json_param_file__clean = None
        else:
            detail = ", ".join(allowed_subcommands)
            msg = f"Unknown subcommand: {subcommand!r}, expected one of {detail}. Check help for more details."
            raise NotImplementedError(msg) from None

        # CLI argument route (non-JSON)
        if json_param_file__clean is None:
            raw_dict = vars(namespace)
            raw_dict = cls._normalise_non_json_namespace_derived_dict(raw_dict)
        # JSON file route
        else:
            raw_dict = _json_helper.load_json_file(json_param_file__clean)

        clean_args = cls.from_dict(raw_dict)
        clean_args._json_params_file = json_param_file__clean
        return clean_args

    @classmethod
    def from_dict(cls, raw_dict: t.Dict[str, t.Any]) -> "CleanArgs":
        dict_validator = ArgDictValidator(raw_dict)
        dict_validator.assert_valid()
        clean_args = cls._from_dict(raw_dict)
        return clean_args

    @classmethod
    def _from_dict(cls, valid_dict: t.Dict[str, t.Any]) -> "CleanArgs":
        is_1_indexed = True

        # Get raw values from dict
        mode__raw = valid_dict[const.JSON_PARAM__MODE]
        input_file__raw = valid_dict[const.ARG_INPUT]
        output_file__raw = valid_dict[const.ARG_OUTPUT]
        summary_file__raw = valid_dict[const.ARG_SUMMARY]
        output_file_delimiter__raw = valid_dict[const.JSON_PARAM__OUTPUT_DELIMITER]
        forced_input_file_delimiter__raw = valid_dict[const.ARG_FORCE_INPUT_DELIMITER]
        forced_header_row_index__raw = valid_dict[const.ARG_FORCE_HEADER_ROW_INDEX]
        reheader_mapping__raw = valid_dict[const.ARG_REHEADER]
        reheader_append__raw = valid_dict[const.ARG_REHEADER_APPEND]
        column_order__raw = valid_dict[const.JSON_PARAM__COLUMN_ORDER]
        required_columns__raw = valid_dict[const.JSON_PARAM__REQUIRED_COLUMNS]
        optional_columns__raw = valid_dict[const.JSON_PARAM__OPTIONAL_COLUMNS]

        # Clean raw values (not columns theyre complex and cleaned below)
        mode = ColumnMode(mode__raw)
        input_file__clean = _clean.InputFile(input_file__raw).clean
        output_file__clean = _clean.OutputFile(input_file__raw, output_file__raw).clean
        summary_file__clean = _clean.SummaryFile(
            input_file__raw, summary_file__raw
        ).clean
        output_file_delimiter__clean = _clean.clean_output_delimiter(
            output_file_delimiter__raw
        )
        forced_input_file_delimiter__clean = _clean.clean_input_delimiter(
            forced_input_file_delimiter__raw
        )
        forced_header_row_index__clean = _clean.clean_index(
            forced_header_row_index__raw
        )
        reheader_append__clean = bool(reheader_append__raw)

        # Clean and parse columns.
        # Then normalise string columns to int columns, if necessary
        parsed_columns = _parser.ParsedColumns(
            column_order=column_order__raw,
            required_columns=required_columns__raw,
            optional_columns=optional_columns__raw,
        )
        parsed_columns.assert_valid()
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
            reheader_mapping__intermediate = cls._parse_and_clean_column_dict(
                reheader_mapping__raw, is_1_indexed
            )
        else:
            column_order__clean = column_order__raw
            required_columns__clean = required_columns__raw
            optional_columns__clean = optional_columns__raw
            reheader_mapping__intermediate = reheader_mapping__raw

        # Finally clean reheader mapping
        reheader_mapping__clean = _clean.clean_reheader(
            reheader_mapping__intermediate,
            column_order__clean,
            mode=mode.value,
            append=reheader_append__clean,
        )

        # Create instance
        instance = cls(
            is_1_indexed=True,
            mode=mode,
            input_file=input_file__clean,
            output_file=output_file__clean,
            summary_file=summary_file__clean,
            column_order=tuple(column_order__clean),
            required_columns=tuple(required_columns__clean),
            optional_columns=tuple(optional_columns__clean),
            output_file_delimiter=output_file_delimiter__clean,
            forced_input_file_delimiter=forced_input_file_delimiter__clean,
            forced_header_row_index=forced_header_row_index__clean,
            reheader_mapping=reheader_mapping__clean,
            reheader_append=reheader_append__clean,
        )
        return instance


class ArgDictValidator:
    """
    Validates a dictionary of arguments, as parsed from a JSON file or the namespace of a CLI command.

    The dictionary is copied internally, so that the original dictionary is not mutated.
    """

    def __init__(self, raw_dict: t.Dict[str, t.Any]) -> None:
        self._raw_dict = copy.deepcopy(raw_dict)

    def assert_valid(self):
        """
        If object (and hence the internal dictionary) is valid, do nothing. Otherwise, raise an exception.
        """
        raw_dict = self._raw_dict
        self._valid_keys(raw_dict)
        self._valid_values(raw_dict)

    def _valid_keys(self, raw_dict: t.Dict[str, t.Any]):
        """
        Assert that raw_dict is a valid dictionary of arguments

        No semantic validation is done here, only syntactic validation.
        """
        NECESSARY_KEYS = [
            const.JSON_PARAM__MODE,
            const.JSON_PARAM__INPUT_FILE,
            const.JSON_PARAM__OUTPUT_FILE,
            const.JSON_PARAM__SUMMARY_FILE,
            const.JSON_PARAM__COLUMN_ORDER,
            const.JSON_PARAM__REQUIRED_COLUMNS,
            const.JSON_PARAM__OPTIONAL_COLUMNS,
            const.JSON_PARAM__REHEADER,
            const.JSON_PARAM__REHEADER_APPEND,
            const.JSON_PARAM__OUTPUT_DELIMITER,
            const.JSON_PARAM__FORCED_INPUT_DELIMITER,
            const.JSON_PARAM__FORCED_HEADER_ROW_INDEX,
        ]
        if set(NECESSARY_KEYS) != raw_dict.keys():
            missing_keys = set(NECESSARY_KEYS) - set(raw_dict.keys())
            msg = f"Cannot parse arguments because the following keys are missing: {missing_keys}"
            raise exc.ValidationError(msg)

    def _valid_values(self, raw_dict: t.Dict[str, t.Any]):
        # Do the validation of each key & its value (but no semantic validation
        # e.g. check the path exists as that is handled downstream)

        # mode
        self._valid_values__mode(raw_dict[const.JSON_PARAM__MODE])

        # input_file, output_file, summary_file
        self._valid_values__input_file(
            raw_dict[const.JSON_PARAM__INPUT_FILE],
        )
        self._valid_values__optional_file(
            raw_dict[const.JSON_PARAM__OUTPUT_FILE],
            key=const.JSON_PARAM__OUTPUT_FILE,
        )
        self._valid_values__optional_file(
            raw_dict[const.JSON_PARAM__SUMMARY_FILE],
            key=const.JSON_PARAM__SUMMARY_FILE,
        )

        # column_order
        self._valid_values__column(
            raw_dict[const.JSON_PARAM__COLUMN_ORDER],
            key=const.JSON_PARAM__COLUMN_ORDER,
        )
        # required_columns
        self._valid_values__column(
            raw_dict[const.JSON_PARAM__REQUIRED_COLUMNS],
            key=const.JSON_PARAM__REQUIRED_COLUMNS,
        )
        # optional_columns
        self._valid_values__column(
            raw_dict[const.JSON_PARAM__OPTIONAL_COLUMNS],
            key=const.JSON_PARAM__OPTIONAL_COLUMNS,
            is_optional=True,
        )

        # reheader
        self._valid_values__reheader(
            raw_dict[const.JSON_PARAM__REHEADER],
            key=const.JSON_PARAM__REHEADER,
            is_optional=True,
        )

        # reheader_append
        self._valid_values__reheader_append(
            raw_dict[const.JSON_PARAM__REHEADER_APPEND],
            key=const.JSON_PARAM__REHEADER_APPEND,
        )

        # output_delimiter
        self._valid_values__delimiter(
            raw_dict[const.JSON_PARAM__OUTPUT_DELIMITER],
            key=const.JSON_PARAM__OUTPUT_DELIMITER,
            is_optional=False,
        )
        # forced_input_delimiter
        self._valid_values__delimiter(
            raw_dict[const.JSON_PARAM__FORCED_INPUT_DELIMITER],
            key=const.JSON_PARAM__FORCED_INPUT_DELIMITER,
            is_optional=True,
        )

        # forced_header_row_index
        self._valid_values__forced_header_row_index(
            raw_dict[const.JSON_PARAM__FORCED_HEADER_ROW_INDEX],
            key=const.JSON_PARAM__FORCED_HEADER_ROW_INDEX,
            is_optional=True,
        )
        return

    @staticmethod
    def _valid_values__mode(mode: str) -> None:
        try:
            _ = ColumnMode(mode)
        except ValueError:
            msg = f"Invalid value for {const.JSON_PARAM__MODE!r}: expected one of {ColumnMode.__members__.keys()!r}, got {mode!r}"
            raise exc.ValidationError(msg)

    @staticmethod
    def _valid_values__input_file(input_file: t.Union[str, Path]) -> None:
        input_file_ = str(input_file) if isinstance(input_file, Path) else input_file
        if isinstance(input_file_, str) and len(input_file_) > 0:
            return
        else:
            msg = f"Invalid value for {const.JSON_PARAM__INPUT_FILE!r}: expected a non-empty string, got {input_file_!r}"
            raise exc.ValidationError(msg)

    @staticmethod
    def _valid_values__optional_file(
        maybe_file: t.Optional[t.Union[str, Path]], key: str
    ) -> None:
        if maybe_file is None:
            return
        maybe_file_ = str(maybe_file) if isinstance(maybe_file, Path) else maybe_file
        if isinstance(maybe_file_, str) and len(maybe_file_) > 0:
            return
        else:
            msg = f"Invalid value for {key!r}: expected a non-empty string or a null-value, got {maybe_file_!r}"
            raise exc.ValidationError(msg)

    @staticmethod
    def _valid_values__column(
        columns: t.Iterable[t.Union[str, int]], key: str, is_optional: bool = False
    ) -> None:
        # Raise an error early if the container is not a list or tuple
        valid_container = isinstance(columns, (list, tuple))
        if not valid_container:
            msg_detail = f"expected either a list or a tuple, got {type(columns)}"
            msg = f"Invalid value for {key!r}: {msg_detail}"
            raise exc.ValidationError(msg)

        if is_optional:
            msg_detail = "expected either an empty list or a non-empty list of strings or integers"
            valid_size = True
        else:
            valid_size = len(columns) > 0 if valid_container else False
            msg_detail = "a non-empty list of strings or integers"
        valid_elements = all([isinstance(c, (str, int)) for c in columns])

        if valid_size and valid_elements:
            return
        else:
            msg = f"Invalid value for {key!r}: {msg_detail}, got {columns!r}"
            raise exc.ValidationError(msg)

    @staticmethod
    def _valid_values__reheader(
        reheader_mapping: t.Dict[t.Union[str, int], str], key: str, is_optional: bool
    ) -> None:
        # Raise an error early if the container is not a dict
        valid_container = isinstance(reheader_mapping, dict)
        if not valid_container:
            msg_detail = f"expected a dictionary, got {type(reheader_mapping)}"
            msg = f"Invalid value for {key!r}: {msg_detail}"
            raise exc.ValidationError(msg)

        valid_keys = all([isinstance(k, (str, int)) for k in reheader_mapping.keys()])
        valid_values = all([isinstance(v, str) for v in reheader_mapping.values()])
        if is_optional:
            msg_detail = "expected either an empty dictionary or a non-empty dictionary"
            valid_size = True
        else:
            valid_size = len(reheader_mapping) > 0 if valid_container else False
            msg_detail = "a non-empty dictionary"
        if valid_keys and valid_values and valid_size:
            return
        else:
            msg = f"Invalid value for {key!r}: {msg_detail}, got {reheader_mapping!r}"
            raise exc.ValidationError(msg)

    @staticmethod
    def _valid_values__delimiter(
        delimiter: t.Optional[str], key: str, is_optional: bool
    ) -> None:
        if is_optional and delimiter is None:
            return
        if is_optional:
            msg_detail = "expected either a non-empty string or a null-value"
        else:
            msg_detail = "a non-empty string"
        valid_size = isinstance(delimiter, str) and len(delimiter) > 0
        if valid_size:
            return
        else:
            msg = f"Invalid value for {key!r}: {msg_detail}, got {delimiter!r}"
            raise exc.ValidationError(msg)

    @staticmethod
    def _valid_values__forced_header_row_index(
        forced_header_row_index: t.Optional[int], key: str, is_optional: bool
    ) -> None:
        if is_optional and forced_header_row_index is None:
            return
        if is_optional:
            msg_detail = "expected either a non-negative integer or a null-value"
        else:
            msg_detail = "a non-negative integer"
        valid_index = (
            isinstance(forced_header_row_index, int) and forced_header_row_index >= 0
        )
        if valid_index:
            return
        else:
            msg = f"Invalid value for {key!r}: {msg_detail}, got {forced_header_row_index!r}"
            raise exc.ValidationError(msg)

    @staticmethod
    def _valid_values__reheader_append(reheader_append: bool, key: str) -> None:
        if isinstance(reheader_append, bool):
            return
        else:
            msg = f"Invalid value for {key!r}: expected a boolean, got {reheader_append!r}"
            raise exc.ValidationError(msg)
