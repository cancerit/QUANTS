import typing as t
import sys

# TODO replace with logging


def display_info(info: str, prefix: str = "Info: ") -> None:
    """
    Prints an info message to stdout, prefixed with "Info: ".
    """
    info_msg = f"{prefix}{info}"
    print(info_msg)


def display_error(error: t.Union[str, Exception], prefix: str = "Error: ") -> None:
    """
    Prints an error message to stderr, prefixed with "Error: ".
    """
    error_msg = f"{prefix}{error}"
    print(error_msg, file=sys.stderr)


def display_warning(warning: str, prefix: str = "Warning: ") -> None:
    """
    Prints an error message to stderr, prefixed with "Warning: ".
    """
    warning_msg = f"{prefix}{warning}"
    print(warning_msg, file=sys.stderr)
