# SPDX-License-Identifier: MPL-2.0
"""Print versions of imported packages."""

from __future__ import annotations

import platform
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import cached_property
from importlib.metadata import packages_distributions, version
from types import MappingProxyType, ModuleType
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from . import _pu
from ._repr import repr_mimebundle as _repr_mimebundle
from ._ttl_cache import ttl_cache
from ._widget import widget as _widget

if TYPE_CHECKING:
    from collections.abc import Collection, Generator, Iterable, Mapping, Sequence
    from collections.abc import Set as AbstractSet

    _TableHeader: TypeAlias = (
        tuple[Literal["Package"], Literal["Version"]]
        | tuple[Literal["Dependency"], Literal["Version"]]
        | tuple[Literal["Component"], Literal["Info"]]
    )


# TODO: make this configurable
# https://github.com/flying-sheep/session-info2/issues/6
IGNORED = frozenset({"ipython", "session-info2"})


@dataclass
class _AdditionalInfo:
    sys: str = field(default_factory=lambda: sys.version.replace("\n", ""))
    os: str | None = field(default_factory=platform.platform)
    cpu: str | None = field(default_factory=_pu.cpu_info)
    gpu: Collection[str] = field(default_factory=_pu.gpu_info)
    date: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    )

    def _table(self) -> Generator[tuple[str, str], None, None]:
        yield ("Python", self.sys)
        if self.os:
            yield ("OS", self.os)
        if self.cpu:
            yield ("CPU", self.cpu)
        for gpu in self.gpu:
            yield ("GPU", gpu)
        yield ("Updated", self.date)


@dataclass(frozen=True)
class SessionInfo:
    """Information about imported packages."""

    pkg2dists: Mapping[str, Sequence[str]]
    user_globals: Mapping[str, Any]
    dependencies: bool | None = None

    info: _AdditionalInfo = field(default_factory=_AdditionalInfo)

    @cached_property
    def dist2pkgs(self) -> Mapping[str, frozenset[str]]:
        """Get mapping of distributions to packages."""
        d2ps: defaultdict[str, set[str]] = defaultdict(set)
        for pkg, dists in self.pkg2dists.items():
            for dist in dists:
                d2ps[dist].add(pkg)
        return MappingProxyType({d: frozenset(pkgs) for d, pkgs in d2ps.items()})

    @cached_property
    def imported_dists(self) -> AbstractSet[str]:
        """Get ordered set of imported distributions."""
        # Use dict for preserving insertion order
        imported: dict[str, None] = {}
        for obj in self.user_globals.values():
            mod_name = _get_module_name(obj)
            dist_name = next(
                (d for mn in _mods(mod_name) for d in self.pkg2dists.get(mn, ())),
                None,
            )
            if dist_name is not None and dist_name.casefold() not in IGNORED:
                imported[dist_name] = None
        return imported.keys()

    @cached_property
    def deps_dists(self) -> AbstractSet[str]:
        """Get ordered set of loaded distributions that aren’t imported."""
        return {
            dist
            for dist, pkgs in self.dist2pkgs.items()
            if pkgs & sys.modules.keys()
            if dist not in self.imported_dists
        }

    def __hash__(self) -> int:
        """Generate hash value."""
        pkg2dists = tuple((pkg, *ds) for pkg, ds in self.pkg2dists.items())
        return hash((pkg2dists, tuple(self.imported_dists), self.dependencies))

    @ttl_cache()
    def _version(self, dist: str) -> str:
        """Get version(s) of imported distribution."""
        v_meta = version(dist)
        vs_attr = {
            pkg_name: v
            for pkg_name in self.dist2pkgs[dist]
            if (pkg := sys.modules.get(pkg_name))
            and (v := getattr(pkg, "__version__", None))
        }
        if all(v_attr == v_meta for v_attr in vs_attr.values()):
            # This branch is also hit if there are no __version__ attributes
            return v_meta
        if len(vs_attr) == 1:
            v_attr = next(iter(vs_attr.values()))
            return f"{v_meta} ({v_attr})"
        return f"{v_meta} ({', '.join(f'{pkg}: {v}' for pkg, v in vs_attr.items())})"

    def _table_parts(
        self, *, deps_default: bool = True
    ) -> dict[_TableHeader, Iterable[tuple[str, str]]]:
        deps: dict[_TableHeader, Iterable[tuple[str, str]]] = {}
        if (
            self.dependencies or (self.dependencies is None and deps_default)
        ) and self.deps_dists:
            deps = {
                ("Dependency", "Version"): (
                    (d, self._version(d)) for d in self.deps_dists
                )
            }
        return {
            ("Package", "Version"): (
                (d, self._version(d)) for d in self.imported_dists
            ),
            **deps,
            ("Component", "Info"): self.info._table(),  # noqa: SLF001
        }

    def __repr__(self) -> str:
        """Generate string representation."""
        return "\n----\t----\n".join(
            part_fmt
            for _, part in self._table_parts(deps_default=False).items()
            if (part_fmt := "\n".join(f"{k}\t{v}" for k, v in part))
        )

    _repr_mimebundle_ = _repr_mimebundle
    widget = _widget


def session_info(
    *,
    os: bool = True,
    cpu: bool = False,
    gpu: bool = False,
    dependencies: bool | None = None,
) -> SessionInfo:
    """Print versions of imported packages."""
    pkg2dists = packages_distributions()
    user_globals = vars(sys.modules["__main__"])
    info = _AdditionalInfo(
        **({} if os else dict(os=None)),  # type: ignore[arg-type]
        **({} if cpu else dict(cpu=None)),  # type: ignore[arg-type]
        **({} if gpu else dict(gpu=())),  # type: ignore[arg-type]
    )
    return SessionInfo(pkg2dists, user_globals, dependencies=dependencies, info=info)


def _get_module_name(obj: object) -> str:
    """Get module name."""
    if isinstance(obj, ModuleType):
        return obj.__name__
    if isinstance(mod := getattr(obj, "__module__", None), str):
        return mod
    return type(obj).__module__


def _mods(mod_name: str) -> Generator[str, None, None]:
    """Generate parent module names, starting with input."""
    parts = mod_name.split(".")
    for i in reversed(range(len(parts))):
        yield ".".join(parts[: i + 1])
