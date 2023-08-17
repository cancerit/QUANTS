import typing as t
from pathlib import Path
import csv
from dataclasses import dataclass
import enum

import pytest
import pandas as pd

from src.dna.helpers import reverse_complement, trim_sequence
from src.csv.csv_helper import (
    find_first_tabular_line_index_and_offset,
    find_column_headers,
)
from pyquest_library_converter import main
from src.args.args_parsing import get_argparser
from src.args.args_cleaner import ArgsCleaner
from src import constants as const
from src.exceptions import ValidationError, NullDataError


# CONSTANTS
EXAMPLE_FORWARD_PRIMER = "AATTGATA"
EXAMPLE_REVERSE_PRIMER = "ACTACGAC"

EXAMPLE_DATA__LONG_SEQUENCE = "AATTGATACGGCGACCACCGATCCTGCGCCTTCTCTCCTCCTCCTCCACACTCCAGGCTGGACCTGTACCGAGCCTCGGGTAAATTTGAGCTTCTTGATAGAATTCTTCCCAAACTCCGAGCAACCAACCACAAAGTGCTGCTGTTCTGTCAGATGACTTCCCTCATGACCATCATGGAAGATTACTTTGCGTATCGCGGCTTTAAATACCTCAGGCTTGATGGTGAGTATGAGCCAGTGAGGCGTTTCTTACAGGGTTTTGTTGTTGTGGCTCGTATGCCGTCTTCTGCTTG"
EXAMPLE_DATA__SHORT_SEQUENCE = "AATTGATAAGGTACCACTACGAC"

EXAMPLE_DATA__LONG_SEQUENCE_TRIMMED, _, _ = trim_sequence(
    EXAMPLE_DATA__LONG_SEQUENCE,
    forward_primer=EXAMPLE_FORWARD_PRIMER,
    reverse_primer=EXAMPLE_REVERSE_PRIMER,
)
EXAMPLE_DATA__SHORT_SEQUENCE_TRIMMED, _, _ = trim_sequence(
    EXAMPLE_DATA__SHORT_SEQUENCE,
    forward_primer=EXAMPLE_FORWARD_PRIMER,
    reverse_primer=EXAMPLE_REVERSE_PRIMER,
)

EXAMPLE_DATE__LONG_SEQUENCE_REV_COMP = reverse_complement(EXAMPLE_DATA__LONG_SEQUENCE)
EXAMPLE_DATE__SHORT_SEQUENCE_REV_COMP = reverse_complement(EXAMPLE_DATA__SHORT_SEQUENCE)
EXAMPLE_DATE__LONG_SEQUENCE_TRIMMED_REV_COMP = reverse_complement(
    EXAMPLE_DATA__LONG_SEQUENCE_TRIMMED
)
EXAMPLE_DATE__SHORT_SEQUENCE_TRIMMED_REV_COMP = reverse_complement(
    EXAMPLE_DATA__SHORT_SEQUENCE_TRIMMED
)

EXAMPLE_DATA__NAME_1 = "ENST00000344626.10.ENSG00000127616.20_chr19:11027766_1del"
EXAMPLE_DATA__NAME_2 = "ENST00000344626.101.ENSG00000127616.20_chr19:11027766_1del"
EXAMPE_HEADER__NAME = "name"
EXAMPE_HEADER__SEQUENCE = "sequence"


# HELPERS
@dataclass
class TabularData:
    input_array: t.List[t.List[str]]
    output_array: t.List[t.List[t.Union[str, int]]]

    @property
    def input_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.input_array[1:], columns=self.input_array[0])

    @property
    def output_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.output_array[1:], columns=self.output_array[0])


class UsePrimers(enum.Enum):
    YES = True
    NO = False


class RevCompFlag(enum.Enum):
    YES = True
    NO = False


class WarnNullData(enum.Enum):
    YES = True
    NO = False


class ShouldRaiseFlag(enum.Enum):
    RAISE = True
    DONT_RAISE = False


class UseHeaders(enum.Enum):
    YES = True
    NO = False


class InputHasColHeaders(enum.Enum):
    YES = True
    NO = False


def adjust_skip_n_rows(
    skip_n_rows: int, input_has_col_headers: InputHasColHeaders
) -> int:
    adjusted = int(input_has_col_headers.value) + skip_n_rows
    return adjusted


# FIXTURES


@pytest.fixture
def get_main_kwargs():
    def _get_main_kwargs(
        input_file: t.Union[str, Path],
        output_file: t.Union[str, Path],
        update_kwargs: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Dict[str, t.Any]:
        default_kwargs = {
            const.KEY_ADJUSTED_SKIP_N_ROWS: 0,
            const._ARG_VERBOSE: False,
            const._ARG_FORWARD_PRIMER: "",
            const._ARG_REVERSE_PRIMER: "",
            const._ARG_NAME_INDEX: 1,  # 1-based indexing
            const._ARG_SEQ_INDEX: 2,  # 1-based indexing
            const._ARG_REVERSE_COMPLEMENT_FLAG: False,
            const._ARG_FORCE_HEADER_INDEX: None,
            const._ARG_WARN_NULL_DATA: False,
        }
        kwargs = default_kwargs.copy()
        if update_kwargs is not None:
            kwargs.update(update_kwargs)
        kwargs[const._ARG_INPUT] = input_file
        kwargs[const._ARG_OUTPUT] = output_file
        return kwargs

    yield _get_main_kwargs


@pytest.fixture
def get_cmd():
    """Return a string of the command to run."""

    def _get_cmd(
        main_kwargs: t.Dict[str, t.Any], use_headers: bool, input_has_col_headers: bool
    ) -> str:
        input_file = main_kwargs[const._ARG_INPUT]
        output_file = main_kwargs[const._ARG_OUTPUT]
        # USAGE: [-v] [--forward FORWARD_PRIMER] [--reverse REVERSE_PRIMER] [--skip SKIP_N_ROWS] [--force-header-index FORCE_HEADER_INDEX] [--revcomp] (-n NAME_HEADER | -N NAME_INDEX) (-s SEQUENCE_HEADER | -S SEQUENCE_INDEX) input output
        cmd = f"{input_file} {output_file}"
        if main_kwargs[const._ARG_VERBOSE]:
            cmd += " -v"
        if main_kwargs[const._ARG_FORWARD_PRIMER]:
            cmd += f" --forward {main_kwargs[const._ARG_FORWARD_PRIMER]}"
        if main_kwargs[const._ARG_REVERSE_PRIMER]:
            cmd += f" --reverse {main_kwargs[const._ARG_REVERSE_PRIMER]}"
        if const._ARG_SKIP_N_ROWS in main_kwargs:  # skip_n_rows can return 0
            cmd += f" --skip {main_kwargs[const._ARG_SKIP_N_ROWS]}"

        # If the file has no headers, but we are using indices we do not need to force the header index (because there are no headers)
        # If the file has headers, but we are using indices we do need to force the header index
        # If the file has no headers, and we are using headers we would need to force the header index --> but will lead to a validation error
        # If the file has headers, and we are using headers we do not need to force the header index
        should_force = input_has_col_headers and not use_headers
        forced_index_1_idx = int(not input_has_col_headers) + 1
        if should_force:
            cmd += f" --force-header-index {forced_index_1_idx}"
        if main_kwargs[const._ARG_REVERSE_COMPLEMENT_FLAG]:
            cmd += " --revcomp"
        if main_kwargs[const._ARG_WARN_NULL_DATA] == True:
            cmd += " --suppress-null-errors"
        if use_headers:
            name_header = EXAMPE_HEADER__NAME
            sequence_header = EXAMPE_HEADER__SEQUENCE
            cmd += f" -n {name_header} -s {sequence_header}"
        else:
            if const._ARG_NAME_INDEX in main_kwargs:  # name_index can return 0
                cmd += f" -N {main_kwargs['name_index']}"
            if const._ARG_SEQ_INDEX in main_kwargs:  # sequence_index can return 0
                cmd += f" -S {main_kwargs['sequence_index']}"
        return cmd

    yield _get_cmd


@pytest.fixture
def get_arg_cleaner(get_cmd):
    def _get_arg_cleaner(
        main_kwargs: t.Dict[str, t.Any], use_headers: bool, input_has_col_headers: bool
    ) -> ArgsCleaner:
        cmd = get_cmd(main_kwargs, use_headers, input_has_col_headers)
        parser = get_argparser()
        namespace = parser.parse_args(cmd.split())
        arg_cleaner = ArgsCleaner(namespace)
        return arg_cleaner

    yield _get_arg_cleaner


@pytest.fixture
def make_csv_file(tmp_path):
    """Create a csv file for testing."""
    tmp_csv = tmp_path / "test.csv"

    def _make_csv_file(csv_file_contents: t.List[t.List[t.Any]], delimiter=",") -> Path:
        with open(tmp_csv, "w") as f:
            writer = csv.writer(f, delimiter=delimiter)
            for row in csv_file_contents:
                safe_row = [str(x) for x in row]
                writer.writerow(safe_row)
        return tmp_csv

    yield _make_csv_file


@pytest.fixture
def read_csv_file():
    """Read a csv file for testing."""

    def _read_csv_file(csv_file_path: Path, delimiter: t.Optional[str] = None):
        if delimiter is None:
            delimiter = const._OUTPUT_DELIMITER
        # We skip the first row because it has a comment ## in it
        df = pd.read_csv(str(csv_file_path), delimiter=delimiter, skiprows=1)
        return df

    yield _read_csv_file


# PARAMS

PARAMS = [
    # Upper case sequence
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.upper()],
                [EXAMPLE_DATA__NAME_2, EXAMPLE_DATA__LONG_SEQUENCE.upper()],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATA__SHORT_SEQUENCE.upper(),
                ],
                [
                    2,
                    EXAMPLE_DATA__NAME_2,
                    EXAMPLE_DATA__LONG_SEQUENCE.upper(),
                ],
            ],
        ),
        ShouldRaiseFlag.DONT_RAISE,
        RevCompFlag.NO,
        UsePrimers.NO,
        id="upper_case_sequence",
    ),
    # Lower case sequence
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.lower()],
                [EXAMPLE_DATA__NAME_2, EXAMPLE_DATA__LONG_SEQUENCE.lower()],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATA__SHORT_SEQUENCE.lower(),
                ],
                [
                    2,
                    EXAMPLE_DATA__NAME_2,
                    EXAMPLE_DATA__LONG_SEQUENCE.lower(),
                ],
            ],
        ),
        ShouldRaiseFlag.DONT_RAISE,
        RevCompFlag.NO,
        UsePrimers.NO,
        id="lower_case_sequence",
    ),
    # Upper case sequence + rev comp
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.upper()],
                [EXAMPLE_DATA__NAME_2, EXAMPLE_DATA__LONG_SEQUENCE.upper()],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATE__SHORT_SEQUENCE_REV_COMP.upper(),
                ],
                [
                    2,
                    EXAMPLE_DATA__NAME_2,
                    EXAMPLE_DATE__LONG_SEQUENCE_REV_COMP.upper(),
                ],
            ],
        ),
        ShouldRaiseFlag.DONT_RAISE,
        RevCompFlag.YES,
        UsePrimers.NO,
        id="upper_case_sequence+revcomp",
    ),
    # Lower case sequence + rev comp
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.lower()],
                [EXAMPLE_DATA__NAME_2, EXAMPLE_DATA__LONG_SEQUENCE.lower()],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATE__SHORT_SEQUENCE_REV_COMP.lower(),
                ],
                [
                    2,
                    EXAMPLE_DATA__NAME_2,
                    EXAMPLE_DATE__LONG_SEQUENCE_REV_COMP.lower(),
                ],
            ],
        ),
        ShouldRaiseFlag.DONT_RAISE,
        RevCompFlag.YES,
        UsePrimers.NO,
        id="lower_case_sequence+revcomp",
    ),
    # Upper case sequence + primers
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.upper()],
                [EXAMPLE_DATA__NAME_2, EXAMPLE_DATA__LONG_SEQUENCE.upper()],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATA__SHORT_SEQUENCE_TRIMMED.upper(),
                ],
                [
                    2,
                    EXAMPLE_DATA__NAME_2,
                    EXAMPLE_DATA__LONG_SEQUENCE_TRIMMED.upper(),
                ],
            ],
        ),
        ShouldRaiseFlag.DONT_RAISE,
        RevCompFlag.NO,
        UsePrimers.YES,
        id="upper_case_sequence+primers",
    ),
    # Lower case sequence + primers
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.lower()],
                [EXAMPLE_DATA__NAME_2, EXAMPLE_DATA__LONG_SEQUENCE.lower()],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATA__SHORT_SEQUENCE_TRIMMED.lower(),
                ],
                [
                    2,
                    EXAMPLE_DATA__NAME_2,
                    EXAMPLE_DATA__LONG_SEQUENCE_TRIMMED.lower(),
                ],
            ],
        ),
        ShouldRaiseFlag.DONT_RAISE,
        RevCompFlag.NO,
        UsePrimers.YES,
        id="lower_case_sequence+primers",
    ),
    # Upper case sequence + rev comp + primers
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.upper()],
                [EXAMPLE_DATA__NAME_2, EXAMPLE_DATA__LONG_SEQUENCE.upper()],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATE__SHORT_SEQUENCE_TRIMMED_REV_COMP.upper(),
                ],
                [
                    2,
                    EXAMPLE_DATA__NAME_2,
                    EXAMPLE_DATE__LONG_SEQUENCE_TRIMMED_REV_COMP.upper(),
                ],
            ],
        ),
        ShouldRaiseFlag.DONT_RAISE,
        RevCompFlag.YES,
        UsePrimers.YES,
        id="upper_case_sequence+revcomp+primers",
    ),
    # Lower case sequence + rev comp + primers
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.lower()],
                [EXAMPLE_DATA__NAME_2, EXAMPLE_DATA__LONG_SEQUENCE.lower()],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATE__SHORT_SEQUENCE_TRIMMED_REV_COMP.lower(),
                ],
                [
                    2,
                    EXAMPLE_DATA__NAME_2,
                    EXAMPLE_DATE__LONG_SEQUENCE_TRIMMED_REV_COMP.lower(),
                ],
            ],
        ),
        ShouldRaiseFlag.DONT_RAISE,
        RevCompFlag.YES,
        UsePrimers.YES,
        id="lower_case_sequence+revcomp+primers",
    ),
]


# TESTS


@pytest.mark.parametrize(
    "tabular_data, should_raise, revcomp_flag, primer_flag", PARAMS
)
@pytest.mark.parametrize(
    "use_column_headers_flag",
    [UseHeaders.YES, UseHeaders.NO],
)
@pytest.mark.parametrize(
    "input_has_col_headers", [InputHasColHeaders.YES, InputHasColHeaders.NO]
)
def test_main(
    tabular_data: TabularData,
    make_csv_file,
    read_csv_file,
    tmp_path,
    get_main_kwargs,
    get_arg_cleaner,
    should_raise: ShouldRaiseFlag,
    revcomp_flag: RevCompFlag,
    primer_flag: UsePrimers,
    use_column_headers_flag: UseHeaders,
    input_has_col_headers: InputHasColHeaders,
):
    """Test that sequences with upper case letters are converted to lower case."""
    # Setup data
    if (
        input_has_col_headers == InputHasColHeaders.NO
        and use_column_headers_flag == UseHeaders.YES
    ):
        should_raise = ShouldRaiseFlag.RAISE

    # Given
    if input_has_col_headers == InputHasColHeaders.NO:
        input_file = make_csv_file(tabular_data.input_array[1:])
    else:
        input_file = make_csv_file(tabular_data.input_array)
    output_file = tmp_path / "test.out.csv"
    forward_primer = EXAMPLE_FORWARD_PRIMER if primer_flag == UsePrimers.YES else ""
    reverse_primer = EXAMPLE_REVERSE_PRIMER if primer_flag == UsePrimers.YES else ""

    main_kwargs = get_main_kwargs(input_file, output_file)
    main_kwargs[const._ARG_REVERSE_COMPLEMENT_FLAG] = revcomp_flag.value
    main_kwargs[const._ARG_FORWARD_PRIMER] = forward_primer
    main_kwargs[const._ARG_REVERSE_PRIMER] = reverse_primer
    main_kwargs[const._ARG_VERBOSE] = False  # Useful for debugging via logs

    # When: running main
    if should_raise == ShouldRaiseFlag.RAISE:
        with pytest.raises(ValidationError):
            _run_main(
                main_kwargs,
                get_arg_cleaner,
                use_column_headers_flag,
                input_has_col_headers,
            )
        return
    else:
        _run_main(
            main_kwargs,
            get_arg_cleaner,
            use_column_headers_flag,
            input_has_col_headers,
        )

    # Then
    actual_df = read_csv_file(output_file)
    # new_input_file = Path.cwd() / "test.in.csv"
    # new_output_file = Path.cwd() / "test.out.csv"
    # new_input_file.write_text(input_file.read_text())
    # new_output_file.write_text(output_file.read_text())
    pd.testing.assert_frame_equal(actual_df, tabular_data.output_df)


def _run_main(
    main_kwargs,
    get_arg_cleaner,
    use_column_headers_flag: UseHeaders,
    input_has_col_headers: InputHasColHeaders,
):
    # When: specialising execution strategies
    ## ! Mimics command line execution but we need set the CMD line args sensibly
    ## ! as our data is too simple that the heuristic can't guess the correct
    ## ! values for the column header so we need to set them explicitly
    ## ! (i.e. we need to set the --force-header-row-index)
    arg_cleaner: ArgsCleaner = get_arg_cleaner(
        main_kwargs,
        use_column_headers_flag == UseHeaders.YES,
        input_has_col_headers == InputHasColHeaders.YES,
    )
    arg_cleaner.validate()
    arg_dict = arg_cleaner.to_clean_dict()
    # When: entering the main function
    main(**arg_dict)
    return


NULL_PARAMS = [
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.upper()],
                [EXAMPLE_DATA__NAME_2, "NULL"],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATA__SHORT_SEQUENCE.upper(),
                ],
            ],
        ),
        ShouldRaiseFlag.RAISE,
        id="NULL_SEQUENCE",
    ),
    pytest.param(
        TabularData(
            input_array=[
                # Header row
                [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
                # Data rows
                [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__SHORT_SEQUENCE.upper()],
                ["NA", EXAMPLE_DATA__LONG_SEQUENCE.upper()],
            ],
            output_array=[
                # Header row
                [
                    const._OUTPUT_HEADER__ID,
                    const._OUTPUT_HEADER__NAME,
                    const._OUTPUT_HEADER__SEQUENCE,
                ],
                # Data rows
                [
                    1,
                    EXAMPLE_DATA__NAME_1,
                    EXAMPLE_DATA__SHORT_SEQUENCE.upper(),
                ],
            ],
        ),
        ShouldRaiseFlag.RAISE,
        id="NULL_NAME",
    ),
]


@pytest.mark.parametrize("tabular_data, should_raise", NULL_PARAMS)
@pytest.mark.parametrize("warn_null", [WarnNullData.YES, WarnNullData.NO])
def test_main__with_null_data(
    get_arg_cleaner,
    tabular_data,
    should_raise,
    make_csv_file,
    tmp_path,
    get_main_kwargs,
    warn_null,
    read_csv_file,
):
    # GIVEN
    input_file = make_csv_file(tabular_data.input_array)
    output_file = tmp_path / "test.out.csv"

    main_kwargs = get_main_kwargs(input_file, output_file)
    main_kwargs[const._ARG_WARN_NULL_DATA] = warn_null.value
    if warn_null == WarnNullData.YES:
        should_raise = ShouldRaiseFlag.DONT_RAISE

    # When: running main
    if should_raise == ShouldRaiseFlag.RAISE:
        with pytest.raises(NullDataError):
            _run_main(
                main_kwargs,
                get_arg_cleaner,
                use_column_headers_flag=UseHeaders.YES,
                input_has_col_headers=InputHasColHeaders.YES,
            )
        return
    else:
        _run_main(
            main_kwargs,
            get_arg_cleaner,
            use_column_headers_flag=UseHeaders.YES,
            input_has_col_headers=InputHasColHeaders.YES,
        )

    # Then
    actual_df = read_csv_file(output_file)
    # new_input_file = Path.cwd() / "test.in.csv"
    # new_output_file = Path.cwd() / "test.out.csv"
    # new_input_file.write_text(input_file.read_text())
    # new_output_file.write_text(output_file.read_text())
    pd.testing.assert_frame_equal(actual_df, tabular_data.output_df)


def test_arg_cleaner_args_vs_main_kwargs(
    make_csv_file, get_arg_cleaner, tmp_path, get_main_kwargs
):
    # Setup data
    input_data = [
        [EXAMPE_HEADER__NAME, EXAMPE_HEADER__SEQUENCE],
        [EXAMPLE_DATA__NAME_1, EXAMPLE_DATA__LONG_SEQUENCE],
    ]

    # Setup main_kwargs
    input_file = make_csv_file(input_data)
    output_file = tmp_path / "test.out.csv"
    main_kwargs = get_main_kwargs(input_file, output_file).copy()
    unadjusted_skip_n_rows = main_kwargs[const.KEY_ADJUSTED_SKIP_N_ROWS]
    adjusted_skip_n_rows = adjust_skip_n_rows(
        unadjusted_skip_n_rows, InputHasColHeaders.YES
    )
    main_kwargs[const.KEY_ADJUSTED_SKIP_N_ROWS] = adjusted_skip_n_rows

    # Setup arg_cleaner args
    arg_cleaner: ArgsCleaner = get_arg_cleaner(
        main_kwargs,
        use_headers=True,
        input_has_col_headers=True,
    )
    arg_cleaner.validate()
    arg_cleaner_args = arg_cleaner.to_clean_dict()

    assert main_kwargs == arg_cleaner_args
