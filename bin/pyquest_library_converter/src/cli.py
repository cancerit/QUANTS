import sys

import typing as t


def display_info(info: str, prefix: str = "Info:") -> None:
    """
    Prints an info message to stdout, prefixed with "Info: ".
    """
    print(_format_msg(info, prefix))


def display_error(error: t.Union[str, Exception], prefix: str = "Error:") -> None:
    """
    Prints an error message to stderr, prefixed with "Error: ".
    """

    print(_format_msg(error, prefix), file=sys.stderr)


def display_warning(warning: str, prefix: str = "Warning:") -> None:
    """
    Prints an error message to stderr, prefixed with "Warning: ".
    """

    print(_format_msg(warning, prefix), file=sys.stderr)


def _format_msg(msg: t.Union[str, Exception], prefix: str) -> str:
    """
    Formats a message with a prefix and a newline.
    """
    prefix = prefix.strip()
    msg = str(msg).strip()
    formatted = " ".join([prefix, msg])
    return formatted
