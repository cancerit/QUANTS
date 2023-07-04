import typing as t

if t.TYPE_CHECKING:
    from pathlib import Path

from src.args.io import (
    finalise_output_file,
)
from src.args import validate


class InputFile:
    """
    Validates an input file.

    A clean input file is a file that exists and is readable.
    """

    def __init__(self, input_file: "Path"):
        self._input_file: "Path" = input_file

    @property
    def clean(self) -> "Path":
        return validate.assert_valid_input_file(self._input_file)


class OutputFile:
    """
    Validates an output file, inferring it from the input file if necessary.

    A clean output file is a file that may not exist but whose parent directory
    is writable.

    Special conditions:
    - If the output file is None, the input file is returned as the clean output file.
    - If the output file is an existing file, it is returned as the clean output file.
    - If the output file is a non-existant file, it is returned as the clean output file.
    - If the output file is an existing directory, that directory and input
        filename are concatenated as clean output file.
    """

    def __init__(self, input_file: "Path", output_file: t.Optional["Path"]):
        self._input_file: "InputFile" = InputFile(input_file)
        self._output_file: t.Optional["Path"] = output_file

    @property
    def clean(self) -> "Path":
        clean_input_file = self._input_file.clean
        output_file = finalise_output_file(clean_input_file, self._output_file)
        return validate.assert_valid_output_file(output_file)
