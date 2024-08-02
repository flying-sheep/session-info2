"""Configuration file for the Sphinx documentation builder."""

from __future__ import annotations

# specify project details
master_doc = "index"
project = "MyST-NB Quickstart"

# basic build settings
extensions = ["myst_nb"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
nitpicky = True
suppress_warnings = ["mystnb.unknown_mime_type"]

# myst_nb settings
nb_execution_mode = "force"
nb_execution_show_tb = True
