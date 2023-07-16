import typing as t
from pathlib import Path
import csv
from dataclasses import dataclass
import enum

import pytest
import pandas as pd

from src.dna.helpers import reverse_complement, trim_sequence
from pyquest_library_converter import main
from src.args.args_parsing import get_argparser
from src.args.args_cleaner import ArgsCleaner
from src import constants as const


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


class UseArgCleanerFlag(enum.Enum):
    YES = True
    NO = False


class UsePrimers(enum.Enum):
    YES = True
    NO = False


class RevCompFlag(enum.Enum):
    YES = True
    NO = False


class ShouldRaiseFlag(enum.Enum):
    RAISE = True
    DONT_RAISE = False


class UseIndices(enum.Enum):
    YES = True
    NO = False


# FIXTURES


@pytest.fixture
def get_main_kwargs():
    def _get_main_kwargs(
        input_file: t.Union[str, Path],
        output_file: t.Union[str, Path],
        update_kwargs: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Dict[str, t.Any]:
        default_kwargs = {
            const._ARG_SKIP_N_ROWS: 1,  # skip header row
            const._ARG_VERBOSE: False,
            const._ARG_FORWARD_PRIMER: "",
            const._ARG_REVERSE_PRIMER: "",
            const._ARG_NAME_INDEX: 1,  # 1-based indexing
            const._ARG_SEQ_INDEX: 2,  # 1-based indexing
            const._ARG_REVERSE_COMPLEMENT_FLAG: False,
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

    def _get_cmd(main_kwargs: t.Dict[str, t.Any], use_indices: bool) -> str:
        input_file = main_kwargs[const._ARG_INPUT]
        output_file = main_kwargs[const._ARG_OUTPUT]
        # USAGE: [-v] [--forward FORWARD_PRIMER] [--reverse REVERSE_PRIMER] [--skip SKIP_N_ROWS] [--revcomp] (-n NAME_HEADER | -N NAME_INDEX) (-s SEQUENCE_HEADER | -S SEQUENCE_INDEX) input output
        cmd = f"{input_file} {output_file}"
        if main_kwargs[const._ARG_VERBOSE]:
            cmd += " -v"
        if main_kwargs[const._ARG_FORWARD_PRIMER]:
            cmd += f" --forward {main_kwargs[const._ARG_FORWARD_PRIMER]}"
        if main_kwargs[const._ARG_REVERSE_PRIMER]:
            cmd += f" --reverse {main_kwargs[const._ARG_REVERSE_PRIMER]}"
        if const._ARG_SKIP_N_ROWS in main_kwargs:  # skip_n_rows can return 0
            cmd += f" --skip {main_kwargs[const._ARG_SKIP_N_ROWS]}"
        if main_kwargs[const._ARG_REVERSE_COMPLEMENT_FLAG]:
            cmd += f" --revcomp"
        if use_indices:
            if const._ARG_NAME_INDEX in main_kwargs:  # name_index can return 0
                cmd += f" -N {main_kwargs['name_index']}"
            if const._ARG_SEQ_INDEX in main_kwargs:  # sequence_index can return 0
                cmd += f" -S {main_kwargs['sequence_index']}"
        else:
            name_header = EXAMPE_HEADER__NAME
            sequence_header = EXAMPE_HEADER__SEQUENCE
            cmd += f" -n {name_header} -s {sequence_header}"
        return cmd

    yield _get_cmd


@pytest.fixture
def get_arg_cleaner(get_cmd):
    def _get_arg_cleaner(
        main_kwargs: t.Dict[str, t.Any], use_indices: bool
    ) -> ArgsCleaner:
        cmd = get_cmd(main_kwargs, use_indices)
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
        df = pd.read_csv(str(csv_file_path), delimiter=delimiter)
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
    "use_arg_cleaner", [UseArgCleanerFlag.YES, UseArgCleanerFlag.NO]
)
@pytest.mark.parametrize(
    "use_column_indices_flag",
    [UseIndices.YES, UseIndices.NO],
)
def test_main(
    tabular_data: TabularData,
    make_csv_file,
    read_csv_file,
    tmp_path,
    get_main_kwargs,
    get_arg_cleaner,
    use_arg_cleaner,
    should_raise: ShouldRaiseFlag,
    revcomp_flag: RevCompFlag,
    primer_flag: UsePrimers,
    use_column_indices_flag,
):
    """Test that sequences with upper case letters are converted to lower case."""
    # Setup data

    # Given
    input_file = make_csv_file(tabular_data.input_array)
    output_file = tmp_path / "test.out.csv"
    forward_primer = EXAMPLE_FORWARD_PRIMER if primer_flag == UsePrimers.YES else ""
    reverse_primer = EXAMPLE_REVERSE_PRIMER if primer_flag == UsePrimers.YES else ""
    skip_n_rows = 1 if use_column_indices_flag == UseIndices.YES else 0

    main_kwargs = get_main_kwargs(input_file, output_file)
    main_kwargs[const._ARG_REVERSE_COMPLEMENT_FLAG] = revcomp_flag.value
    main_kwargs[const._ARG_FORWARD_PRIMER] = forward_primer
    main_kwargs[const._ARG_REVERSE_PRIMER] = reverse_primer
    main_kwargs[const._ARG_VERBOSE] = False  # Useful for debugging via logs

    # When: differing execution strategies
    if use_arg_cleaner == UseArgCleanerFlag.YES:
        main_kwargs[const._ARG_SKIP_N_ROWS] = skip_n_rows
        # Mimics command line execution
        arg_cleaner: ArgsCleaner = get_arg_cleaner(
            main_kwargs, use_column_indices_flag == UseIndices.YES
        )
        arg_cleaner.validate()
        main(**arg_cleaner.to_clean_dict())
    else:
        main_kwargs[
            const._ARG_SKIP_N_ROWS
        ] = 1  # Main is only column indices so must skip header
        # Directly call main
        main(**main_kwargs)

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
    main_kwargs = get_main_kwargs(input_file, output_file)

    # Setup arg_cleaner args
    arg_cleaner: ArgsCleaner = get_arg_cleaner(main_kwargs, use_indices=True)
    arg_cleaner.validate()
    arg_cleaner_args = {
        "input_file": arg_cleaner.get_clean_input(),
        "skip_n_rows": arg_cleaner.get_clean_skip_n_rows(),
        "output_file": arg_cleaner.get_clean_output(),
        "verbose": arg_cleaner.get_clean_verbose(),
        "forward_primer": arg_cleaner.get_clean_forward_primer(),
        "reverse_primer": arg_cleaner.get_clean_reverse_primer(),
        "name_index": arg_cleaner.get_clean_name_index(),
        "sequence_index": arg_cleaner.get_clean_sequence_index(),
        "reverse_complement_flag": arg_cleaner.get_clean_reverse_complement_flag(),
    }

    assert main_kwargs == arg_cleaner_args
