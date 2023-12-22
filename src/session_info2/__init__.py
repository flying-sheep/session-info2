"""Print versions of imported packages."""
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from importlib.metadata import packages_distributions, version
from types import ModuleType
from typing import Any


@dataclass
class SessionInfo:
    """Information about imported packages."""

    pkg2dists: Mapping[str, Sequence[str]]
    user_globals: Mapping[str, Any]

    @cached_property
    def imported_dists(self) -> Sequence[str]:
        """Calculate package versions."""
        imported: list[str] = []
        for obj in self.user_globals.values():
            mod_name = _get_module_name(obj)
            if mod_name in self.pkg2dists:
                imported.extend(self.pkg2dists[mod_name])
        return imported

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
    if isinstance(obj, type):
        return obj.__module__
    if hasattr(obj, "__module__"):
        return obj.__module__
    return type(obj).__module__
