"""Configuration file for the Sphinx documentation builder."""

from __future__ import annotations

from importlib.metadata import metadata

try:
    import sphinx_build_compatibility as sbc  # type: ignore[import-not-found]
except ImportError:
    sbc = None

_info = metadata("session_info2")

# specify project details
master_doc = "index"
project = _info.get("Name")

# basic build settings
html_theme = "furo"
extensions = ["myst_nb", *(["sphinx_build_compatibility.extension"] if sbc else [])]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
nitpicky = True
suppress_warnings = ["mystnb.unknown_mime_type"]

# myst_nb settings
nb_execution_mode = "cache"
nb_execution_show_tb = True
