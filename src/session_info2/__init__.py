"""Print versions of imported packages."""
from __future__ import annotations

import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import cached_property
from importlib.metadata import packages_distributions, version
from multiprocessing import cpu_count
from types import ModuleType
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from ._repr import repr_mimebundle as _repr_mimebundle
from ._widget import widget as _widget

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Mapping, Sequence
    from collections.abc import Set as AbstractSet

    _TableHeader: TypeAlias = (
        tuple[Literal["Package"], Literal["Version"]]
        | tuple[Literal["Component"], Literal["Info"]]
    )


# TODO: make this configurable
# https://github.com/flying-sheep/session-info2/issues/6
IGNORED = frozenset({"ipython"})


@dataclass
class _AdditionalInfo:
    @staticmethod
    def _cpu_info() -> str:
        """Get CPU info."""
        proc = platform.processor() or None
        return f"{cpu_count()} logical CPU cores{f', {proc}' if proc else ''}"

    sys: str = field(default_factory=lambda: sys.version.replace("\n", ""))
    os: str | None = field(default_factory=platform.platform)
    cpu: str | None = field(default_factory=_cpu_info)
    date: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    )

    def _table(self) -> Generator[tuple[str, str], None, None]:
        yield ("Python", self.sys)
        if self.os:
            yield ("OS", self.os)
        if self.cpu:
            yield ("CPU", self.cpu)
        yield ("Updated", self.date)


@dataclass(frozen=True)
class SessionInfo:
    """Information about imported packages."""

    pkg2dists: Mapping[str, Sequence[str]]
    user_globals: Mapping[str, Any]

    info: _AdditionalInfo = field(default_factory=_AdditionalInfo)

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

    def __hash__(self) -> int:
        """Generate hash value."""
        pkg2dists = tuple((pkg, *ds) for pkg, ds in self.pkg2dists.items())
        return hash((pkg2dists, tuple(self.imported_dists)))

    def _table_parts(self) -> dict[_TableHeader, Iterable[tuple[str, str]]]:
        return {
            ("Package", "Version"): ((d, str(version(d))) for d in self.imported_dists),
            ("Component", "Info"): self.info._table(),  # noqa: SLF001
        }

    def __repr__(self) -> str:
        """Generate string representation."""
        return "\n----\t----\n".join(
            part_fmt
            for _, part in self._table_parts().items()
            if (part_fmt := "\n".join(f"{k}\t{v}" for k, v in part))
        )

    _repr_mimebundle_ = _repr_mimebundle
    widget = _widget


def session_info(*, os: bool = True, cpu: bool = False) -> SessionInfo:
    """Print versions of imported packages."""
    pkg2dists = packages_distributions()
    user_globals = vars(sys.modules["__main__"])
    info = _AdditionalInfo(
        **({} if os else dict(os=None)),  # type: ignore[arg-type]
        **({} if cpu else dict(cpu=None)),  # type: ignore[arg-type]
    )
    return SessionInfo(pkg2dists, user_globals, info=info)


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
