import sys
import warnings
import typing as t


def display_info(info: str, prefix: str = "INFO:") -> None:
    """
    Prints an info message to stdout, prefixed with "Info: ".
    """
    for line in info.split("\n"):
        print(_format_msg(line, prefix))


def display_error(error: t.Union[str, Exception], prefix: str = "ERROR:") -> None:
    """
    Prints an error message to stderr, prefixed with "Error: ".
    """

    print(_format_msg(error, prefix), file=sys.stderr)


def display_warning(warning: str, prefix: str = "WARNING:") -> None:
    """
    Prints an error message to stderr, prefixed with "Warning: ".
    """

    warnings.warn(_format_msg(warning, prefix))


def _format_msg(msg: t.Union[str, Exception], prefix: str) -> str:
    """
    Formats a message with a prefix and a newline.
    """
    prefix = prefix.strip()
    msg = str(msg).strip()
    formatted = " ".join([prefix, msg])
    return formatted


def _simple_warning(message: str, *args, **kwargs):
    print(message, file=sys.stderr)


warnings.showwarning = _simple_warning
