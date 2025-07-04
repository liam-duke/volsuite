# General functions

from pathlib import Path
import sys
from datetime import datetime
from rich.console import Console
import shlex

# Initialize rich printing
console = Console()


def get_base_path():
    """
    Get base path depending on whether the program is running as a script or an exe.
    """
    if getattr(sys, "frozen", False):
        # Navigate to parent folder of volsuite.exe
        return Path(sys.executable).parent
    else:
        # Navigate to src\ folder
        return Path(__file__).resolve().parent.parent


def parse_line(line: str):
    """
    Parse a string into arguments and flags (identified by the use of '=' in a token) separated by spaces.

    Args:
        line: String to be parsed.

    Returns:
        args: A list of string arguments.
        flags: A dictionary mapping flags (substring to the left of '=') to their value (substring to the right of '=').
    """
    tokens = line.strip()
    try:
        tokens = shlex.split(tokens)
    except ValueError as e:
        console_error(e)
    if not tokens:
        return [], {}

    args = []
    flags = {}

    for token in tokens:
        if token.startswith("--"):
            if "=" in token:
                flag, value = token.split("=", 1)
                flags[flag] = value
            else:
                flag, value = token, 1
        elif token.startswith("-"):
            flags[token] = True
        else:
            args.append(token)

    return args, flags


def is_date(date_str: str):
    """
    Validate that a string is written in correct ISO date format.

    Args:
        date_str: String to be validated.

    Returns:
        True if the date is formatted correctly otherwise false.
    """
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def console_error(error: Exception):
    """
    Custom handling of error printing to be used in try-except blocks.

    Args:
        error: Exception to be printed.
    """
    console.print(f"[red]Error: {str(error).capitalize()}.")


def type_eval(s: str):
    """
    Evaluate string with type conversion to int, float, bool or list.

    Args:
        s: String to be converted
    """
    pass
