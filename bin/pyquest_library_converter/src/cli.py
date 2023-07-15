import sys


def display_error(prefix: str, error: Exception) -> None:
    """
    Display the error message.
    """
    error_msg = f"{prefix} {error}"
    print(error_msg, file=sys.stderr)
