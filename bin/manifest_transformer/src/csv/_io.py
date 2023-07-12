import typing as t
import tempfile
from pathlib import Path
import shutil

if t.TYPE_CHECKING:
    import io


def write_output_file(output_io: "io.StringIO", output_file: "Path"):
    with tempfile.NamedTemporaryFile(delete=True) as temp_handle:
        temp_file = Path(temp_handle.name)

        # Write the output to the temporary file
        with temp_file.open("w") as temp_io:
            temp_io.write(output_io.getvalue())

        # Copy the temporary file to the output file
        shutil.copy(temp_file, output_file)
    return
