"""Print versions of imported packages."""
import sys
from collections.abc import Generator, Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from functools import cached_property
from importlib.metadata import packages_distributions, version
from types import ModuleType
from typing import Any

# TODO: make this configurable
# https://github.com/flying-sheep/session-info2/issues/6

IGNORED = frozenset({"ipython"})


@dataclass
class SessionInfo:
    """Information about imported packages."""

    pkg2dists: Mapping[str, Sequence[str]]
    user_globals: Mapping[str, Any]

    @cached_property
    def imported_dists(self) -> AbstractSet[str]:
        """Calculate package versions."""
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

    def __repr__(self) -> str:
        """Generate string representation."""
        return "\n".join(f"{d}\t{version(d)}" for d in self.imported_dists)


def session_info() -> SessionInfo:
    """Print versions of imported packages."""
    pkg2dists = packages_distributions()
    user_globals = vars(sys.modules["__main__"])
    return SessionInfo(pkg2dists, user_globals)


def _get_module_name(obj: Any) -> str:  # noqa: ANN401
    """Get module name."""
    if isinstance(obj, ModuleType):
        return obj.__name__
    if hasattr(obj, "__module__"):
        return obj.__module__
    return type(obj).__module__


def _mods(mod_name: str) -> Generator[str, None, None]:
    """Generate parent module names, starting with input."""
    parts = mod_name.split(".")
    for i in reversed(range(len(parts))):
        yield ".".join(parts[: i + 1])
