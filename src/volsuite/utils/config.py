import json
from pathlib import Path
from rich.console import Console

console = Console()

# Default configuration settings

DEFAULT_CONFIG = {
    "DEFAULT_TICKER": None,
    "EXPORT_FOLDER": "exports",
    "HV_ROLLING_WINDOWS": [5, 10, 20, 50],
    "IV_SURFACE_CMAP": "jet",
    "IV_SURFACE_STRIKE_RANGE": 0.2,
    "IV_SURFACE_RESOLUTION": 25,
    "DISPLAY_MAX_ROWS": 0,
    "DISPLAY_MAX_COLUMN_WIDTH": 0,
}


# Configuration utilities


def load_config(config_path):
    """
    Load config.json from the given path.

    Args:
        config_path: Path to config file as a pathlib._local.WindowsPath object.

    Returns:
        Config file as a dictionary.
    """
    with config_path.open("r") as f:
        config = json.load(f)

    return config


def create_config(config_path):
    """
    Create new config.json from default.

    Args:
        config_path: Path of new config.json as a pathlib._local.WindowsPath object.
    """

    # Create new config.json
    with config_path.open("w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
        console.print(
            f"Info: No config.json file found on startup, created default config.json at '{config_path}'."
        )


def init_config(config_path):
    """
    Initialize config file by first attempting to load from the given config path and creating a new file then reloading if necessary.

    Args:
        config_path: Path to config file as a pathlib._local.WindowsPath object.
        config_template: Dictionary config to be copied.

    Returns:
        Config file as a dictionary.
    """
    try:
        config = load_config(config_path)

    except (json.JSONDecodeError, FileNotFoundError):
        create_config(config_path)
        config = load_config(config_path)

    return config
