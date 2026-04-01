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

"""Settings.

ConfZ is a configuration management library for Python based on pydantic.
https://github.com/Zuehlke/ConfZ

Tomli-W is a TOML writer
https://github.com/hukkin/tomli-w
"""
from pathlib import Path
import os
import sys
import subprocess

from platformdirs import user_config_dir
from platformdirs import user_cache_dir
from pydantic import Field
from pydantic import ConfigDict
from confz import BaseConfig, FileSource
import tomli_w
from prettytable import PrettyTable

APP_NAME = "pydna_utils"
CONFIG_PATH = Path(user_config_dir(APP_NAME)) / "pydna_config.toml"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
USER_CACHE_DIR = Path(user_cache_dir(APP_NAME))
USER_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _open_folder(pth):
    """docstring."""
    if sys.platform == "win32":
        subprocess.run(["start", pth], shell=True)
    elif sys.platform == "darwin":
        subprocess.run(["open", "-e", pth])
    else:
        try:
            subprocess.run(["xdg-open", pth])
        except OSError:
            return "no folder to open."

def open_current_folder():
    return _open_folder(os.getcwd())

def open_cache_folder(pth = USER_CACHE_DIR):
    return _open_folder(pth)

def open_config_file(pth = CONFIG_PATH):
    return _open_folder(pth)

def tabulate_settings() -> PrettyTable:
    """Ascii table containing pydna settings."""

    # Convert Pydantic model to dict
    data = load_settings()

    # Create and populate the table
    table = PrettyTable()
    table.field_names = ["Setting", "Value"]

    for key, value in data.dict().items():
        table.add_row([key, value])

    # formatting
    table.align["Setting"] = "l"
    table.align["Value"] = "l"

    return table

class Settings(BaseConfig):
    # allow attribute assignment
    model_config = ConfigDict(frozen=False)

    # your persistent strings (defaults as given)
    pydna_ape_cmd: str = Field(
        default='/usr/bin/tclsh /home/bjorn/.ApE/ApE.tcl'
    )
    pydna_snapgene_cmd: str = Field(
        default='/opt/gslbiotech/snapgene/snapgene.sh'
    )
    pydna_enzymes: str = Field(
        default='/home/bjorn/.ApE/Enzymes/LGM_group.txt'
    )
    pydna_primers: str = Field(
        default='/home/bjorn/myvault/PRIMERS.md'
    )
    pydna_email: str = Field(
        default="someone@example.com"
    )
    pydna_ncbi_cache_dir: str = Field(
        default=str(USER_CACHE_DIR)
    )
    pydna_ncbi_expiration: str = Field(
        default= str(7 * 24 * 3600) # seven days
    )
    # ConfZ v2: use FileSource and mark it optional for first run
    CONFIG_SOURCES = FileSource(file=CONFIG_PATH, optional=True)

def load_settings() -> Settings:
    """Load from file if present; otherwise use defaults in class."""
    return Settings()  # ConfZ loads from CONFIG_SOURCES lazily

def save_settings(cfg: Settings) -> None:
    """Persist current settings to TOML."""
    data = cfg.model_dump()
    with CONFIG_PATH.open("wb") as f:
        tomli_w.dump(data, f)
