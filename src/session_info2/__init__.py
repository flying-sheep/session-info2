"""Print versions of imported packages."""
from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass
from functools import cached_property
from importlib.metadata import packages_distributions, version
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Container, Generator, Mapping, Sequence
    from collections.abc import Set as AbstractSet

    from ipywidgets import Widget

# TODO: make this configurable
# https://github.com/flying-sheep/session-info2/issues/6
IGNORED = frozenset({"ipython"})
MIME_WIDGET = "application/vnd.jupyter.widget-view+json"


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

    def _repr_markdown_(self) -> str:
        # TODO: implement Markdown
        # https://github.com/flying-sheep/session-info2/issues/3
        return repr(self)

    def _repr_mimebundle_(
        self,
        include: Container[str] | None = None,
        exclude: Container[str] | None = None,
        **_kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any]:
        mb: dict[str, Any] = {}
        for mime, d in (
            ("text/plain", self.__repr__),
            ("text/markdown", self._repr_markdown_),
            (MIME_WIDGET, lambda: self.widget()._repr_mimebundle_()[MIME_WIDGET]),  # noqa: SLF001
        ):
            if include is not None and mime not in include:
                continue
            if exclude is not None and mime in exclude:
                continue
            try:
                mb[mime] = d()
            except ImportError:
                traceback.print_exc()
        return mb

    def widget(self) -> Widget:
        """Generate HTML representation."""
        import ipywidgets as widgets

        rows = "\n".join(
            f"<tr><td>{d}</td><td>{version(d)}</td></tr>" for d in self.imported_dists
        )
        html = f"""
        <table class=table>
            <tr><th>Package</th><th>Version</th></tr>
            {rows}
        </table>
        """.strip()
        table = widgets.HTML(value=html)

        try:
            # TODO: replace with client-side copying
            # https://github.com/jupyter-widgets/ipywidgets/issues/1891
            import pyperclip
        except ImportError:
            return table

        button = widgets.Button(
            description="Copy as Markdown",
            icon="copy",
        )
        button.on_click(lambda _: pyperclip.copy(self._repr_markdown_()))
        return widgets.VBox((button, table))


def session_info() -> SessionInfo:
    """Print versions of imported packages."""
    pkg2dists = packages_distributions()
    user_globals = vars(sys.modules["__main__"])
    return SessionInfo(pkg2dists, user_globals)


def _get_module_name(obj: Any) -> str:  # noqa: ANN401
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
