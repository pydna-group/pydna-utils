#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Björn Johansson"
__copyright__ = "Copyright 2013 - 2025 Björn Johansson"
__credits__ = ["Björn Johansson"]
__license__ = "BSD"
__maintainer__ = "Björn Johansson"
__email__ = "bjorn_johansson@bio.uminho.pt"
__status__ = "Development"  # "Production" #"Prototype"
__version__ = "0.0.0"

import os as _os
import sys as _sys
import subprocess as _subprocess
from .settings import load_settings
from .settings import CONFIG_PATH
from prettytable import PrettyTable

cfg = load_settings()

def open_folder(pth):
    """docstring."""
    if _sys.platform == "win32":
        _subprocess.run(["start", pth], shell=True)
    elif _sys.platform == "darwin":
        _subprocess.run(["open", pth])
    else:
        try:
            _subprocess.run(["xdg-open", pth])
        except OSError:
            return "no cache to open."

def open_current_folder():
    return open_folder(_os.getcwd())

# def open_cache_folder():
#     return open_folder(_os.environ["pydna_data_dir"])

def open_config_folder(pth = CONFIG_PATH):
    return open_folder(pth)

cfg = load_settings()

def get_env(cfg = cfg):
    """Create an ascii table containing pydna settings.

    Pydna related variables have names that starts with `pydna_`
    """

    # Convert Pydantic model to dict
    data = cfg.model_dump()

    # Create and populate the table
    table = PrettyTable()
    table.field_names = ["Setting", "Value"]

    for key, value in data.items():
        table.add_row([key, value])

    # formatting
    table.align["Setting"] = "l"
    table.align["Value"] = "l"

    return table
