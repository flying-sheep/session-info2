# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import re
from importlib.metadata import Distribution, distributions
from importlib.metadata import packages_distributions as pkgs_dists
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping


def packages_distributions() -> Mapping[str, list[str]]:
    """Return a mapping of top-level packages to their distributions.

    Unlike :func:`importlib.metadata.packages_distributions`,
    this includes editable packages.
    """
    pds = dict(pkgs_dists())
    for dist in distributions():
        for pkg_name in _top_level_editable(dist):
            if "." not in pkg_name:  # apparently that’s what makes an importable name
                pds.setdefault(pkg_name, []).append(dist.name)
    return pds


def _top_level_editable(dist: Distribution) -> Generator[str, None, None]:
    """Find top-level packages in an editable distribution."""
    for pth_file in dist.files or ():
        if len(pth_file.parts) != 1 or pth_file.suffix != ".pth":
            continue
        for line in pth_file.read_text().splitlines():
            if re.match(r"import\s", line):
                continue  # https://docs.python.org/3/library/site.html
            for p in Path(line).iterdir():
                yield from _find_top_level(p)


def _find_top_level(root: Path) -> Generator[str, None, None]:
    if root.suffix == ".py" and "." not in root.stem and root.is_file():
        yield root.stem
        return
    if "." in root.name or not root.is_dir():
        return
    if (root / "__init__.py").is_file():
        yield root.name
        return
    for p in root.iterdir():
        for pkg in _find_top_level(p):
            yield f"{root.name}.{pkg}"
