# Config related

import json
from pathlib import Path
from rich.console import Console

console = Console()

# Default configuration settings

DEFAULT_CONFIG = {
    "default_ticker": "",
    "display_max_colwidth": 50,
    "display_max_rows": 50,
    "export_folder": "exports",
    "hv_rolling_windows": [5, 10, 20, 50],
    "iv_strike_range": 0.2,
    "iv_surface_cmap": "jet",
    "iv_surface_res": 25,
    "plot_grid": False,
    "plot_legend": False,
    "plot_style": "default",
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
