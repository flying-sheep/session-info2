# SPDX-License-Identifier: MPL-2.0
"""Configuration file for the Sphinx documentation builder."""

from __future__ import annotations

import os
from importlib.metadata import metadata
from shutil import which
from subprocess import run

_info = metadata("session_info2")
_branch = os.environ.get("READTHEDOCS_GIT_IDENTIFIER", "main")
_gh_user, _gh_repo = "flying-sheep", "session-info2"

# specify project details
master_doc = "index"
project = _info.get("Name")

# basic build settings
html_theme = "furo"
html_static_path = ["_static"]
html_css_files = [
    "custom.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.9.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.9.0/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.9.0/css/brands.min.css",
]
html_theme_options = dict(
    source_repository=f"https://github.com/{_gh_user}/{_gh_repo}/",
    source_branch=_branch,
    source_directory="docs/",
)
html_context = dict(
    READTHEDOCS=bool(os.environ.get("READTHEDOCS", "")),
    display_github=True,
    github_user=_gh_user,
    github_repo=_gh_repo,
    github_version=_branch,
)
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx_codeautolink",
    "myst_nb",
]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
nitpicky = True

intersphinx_mapping = dict(
    python=("https://docs.python.org/3/", None),
    ipywidgets=("https://ipywidgets.readthedocs.io/en/stable/", None),
)

always_use_bars_union = True
typehints_defaults = "comma"

# myst_nb settings
nb_execution_mode = "force"
nb_execution_show_tb = True
# For debugging: nb_execution_timeout = -1

# https://github.com/executablebooks/MyST-NB/issues/574
print(which("hatch"))  # noqa: T201
run(["hatch", "-v", "run", "notebook:install-kernel"], check=True)
