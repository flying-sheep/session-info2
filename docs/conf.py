"""Configuration file for the Sphinx documentation builder."""

from __future__ import annotations

from importlib.metadata import metadata
from importlib.util import find_spec

_sbc = (
    ["sphinx_build_compatibility.extension"]
    if find_spec("sphinx_build_compatibility")
    else []
)

_info = metadata("session_info2")

# specify project details
master_doc = "index"
project = _info.get("Name")

# basic build settings
html_theme = "furo"
extensions = ["myst_nb", *_sbc]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
nitpicky = True
suppress_warnings = ["mystnb.unknown_mime_type"]

# myst_nb settings
nb_execution_mode = "cache"
nb_execution_show_tb = True
# For debugging: nb_execution_timeout = -1
