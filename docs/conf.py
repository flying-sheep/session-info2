"""Configuration file for the Sphinx documentation builder."""

from __future__ import annotations

import os
from importlib.metadata import metadata

_info = metadata("session_info2")

# specify project details
master_doc = "index"
project = _info.get("Name")

# theme settings
html_theme = "furo"
if clone_url := os.environ.get("READTHEDOCS_GIT_CLONE_URL"):
    _github_user, _github_repo = clone_url.removesuffix(".git").split("/")[-2:]
    _github_version = os.environ["READTHEDOCS_GIT_IDENTIFIER"]
    html_context = dict(
        READTHEDOCS=True,
        display_github=True,
        github_user=_github_user,
        github_repo=_github_repo,
        github_version=_github_version,
    )
    html_theme_options = dict(
        source_repository=f"https://github.com/{_github_user}/{_github_repo}/",
        source_branch=_github_version,
        source_directory="docs/",
    )

# basic build settings
html_theme = "furo"
extensions = ["myst_nb"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
nitpicky = True
suppress_warnings = ["mystnb.unknown_mime_type"]

# myst_nb settings
nb_execution_mode = "cache"
nb_execution_show_tb = True
