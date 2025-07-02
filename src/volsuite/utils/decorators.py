# Decorators for repeated command functionality

from curl_cffi.requests.exceptions import HTTPError
from functools import wraps
from rich.console import Console

# Initialize rich printing
console = Console()


def catch_network_error(func):
    """
    Decorator to catch yfinance network errors.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except HTTPError:
            console.print(
                f"[red]Error: Unable to fetch data from yfinance API. Check your connection and/or that the input was entered correctly."
            )

    return wrapper


def requires_ticker(func):
    """
    Decorator to prevent running a command without first defining a ticker for the session.
    """

    @wraps(func)
    def wrapper(self, line):
        if not self._ticker:
            console.print(
                "[red]Error: No ticker selected. Specify one using 'ticker <symbol>'."
            )
            return
        return func(self, line)

    return wrapper


def requires_min_args(min_args):
    """
    Wrapper to check for minimum number of arguments before running command.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, line):
            args = line.strip().split()
            if len(args) < min_args:
                console.print(
                    f"[red]'{func.__name__[3:]}' requires at least {(min_args - len(args))} more positional argument(s). Type 'help {func.__name__[3:]}' for correct usage."
                )
                return
            return func(self, line)

        return wrapper

    return decorator
