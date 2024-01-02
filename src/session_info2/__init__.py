"""Print versions of imported packages."""
from __future__ import annotations

import json
import platform
import sys
import traceback
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import cache, cached_property
from importlib.metadata import packages_distributions, version
from multiprocessing import cpu_count
from textwrap import dedent, indent
from types import ModuleType
from typing import TYPE_CHECKING, Any, Literal, cast

if TYPE_CHECKING:
    from collections.abc import Container, Generator, Mapping, Sequence
    from collections.abc import Set as AbstractSet

    from ipywidgets import Widget

# TODO: make this configurable
# https://github.com/flying-sheep/session-info2/issues/6
IGNORED = frozenset({"ipython"})
MIME_WIDGET = "application/vnd.jupyter.widget-view+json"


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

    def __hash__(self) -> int:
        """Generate hash value."""
        pkg2dists = tuple((pkg, *ds) for pkg, ds in self.pkg2dists.items())
        return hash((pkg2dists, tuple(self.imported_dists)))

    def _table_parts(
        self,
    ) -> dict[tuple[str, str], Iterable[tuple[str, str]]]:
        return {
            ("Package", "Version"): ((d, str(version(d))) for d in self.imported_dists),
            ("Component", "Info"): self.info._table(),  # noqa: SLF001
        }

    @cache  # type: ignore[misc,unused-ignore]
    def __repr__(self) -> str:
        """Generate string representation."""
        return "\n----\t----\n".join(
            "\n".join(f"{k}\t{v}" for k, v in part)
            for _, part in self._table_parts().items()
        )

    @cache
    def _repr_markdown_(self) -> str:
        """Generate Markdown representation."""
        # no extra lines possible in markdown tables, so do multiple tables
        return "\n\n".join(
            part
            for header, rows in self._table_parts().items()
            if (part := self._fmt_markdown(header, rows))
        )

    @staticmethod
    def _fmt_markdown(header: tuple[str, str], rows: Iterable[tuple[str, str]]) -> str:
        rows = list(rows)
        if not rows:
            return ""
        widths = [
            max(len(e) for e in col) for col in zip(*(header, *rows), strict=True)
        ]
        row_template = "| " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"
        sep = row_template.format(*(("-" * w) for w in widths))
        rows_fmt = "\n".join(row_template.format(*row) for row in rows)
        return f"{row_template.format(*header)}\n{sep}\n{rows_fmt}"

    @cache
    def _repr_html_(self, *, add_details: bool = True) -> str:
        """Generate static HTML representation."""
        rows = "\n".join(
            part
            for header, rows in self._table_parts().items()
            if (part := self._fmt_html(header, rows))
        )
        table = dedent(
            f"""
            <table class=table>
                {indent(rows, "    ")}
            </table>
            """,
        ).strip()
        if not add_details:
            return table
        return dedent(
            f"""
            {table}
            <details>
                <summary>Copyable Markdown</summary>
                <pre>{self._repr_markdown_()}</pre>
            </details>
            """,
        ).strip()

    @staticmethod
    def _fmt_html(header: tuple[str, str], rows: Iterable[tuple[str, str]]) -> str:
        trs = "\n".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows)
        if not trs:
            return ""
        th = f"<tr><th>{header[0]}</th><th>{header[1]}</th></tr>"
        return f"{th}\n{trs}"

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
            ("text/html", self._repr_html_),
            (MIME_WIDGET, lambda: self.widget()._repr_mimebundle_()[MIME_WIDGET]),  # noqa: SLF001
        ):
            if include is not None and mime not in include:
                continue
            if exclude is not None and mime in exclude:
                continue
            try:
                mb[mime] = cast(Callable[[], str], d)()
            except ImportError:
                traceback.print_exc()
        return mb

    def widget(self) -> Widget:
        """Generate interactive HTML representation."""
        import ipywidgets as widgets

        try:
            from IPython.display import Javascript  # type: ignore[import-not-found]
        except ImportError:
            return widgets.HTML(value=self._repr_html_())

        button = widgets.Button(
            description="Copy as Markdown",
            icon="copy",
        )
        output = widgets.Output(layout=widgets.Layout(display="none"))
        copy_md = Javascript(self._clipboard_js("text/markdown"))

        def on_click(_: widgets.Button) -> None:
            output.clear_output()
            output.append_display_data(copy_md)

        button.on_click(on_click)

        table = widgets.HTML(value=self._repr_html_(add_details=False))
        return widgets.VBox((button, output, table))

    @cache
    def _clipboard_js(
        self,
        rep: Literal["text/plain", "text/markdown", "text/html", "application/json"],
    ) -> str:
        """Javascript to copy representation to clipboard."""
        match rep:
            case "text/plain":
                r = repr(self)
            case "text/markdown":
                r = self._repr_markdown_()
            case "text/html":
                r = self._repr_html_()
            case "application/json":
                parts = self._table_parts()
                r = json.dumps(
                    dict(
                        packages=[
                            dict(package=k, version=v)
                            for k, v in parts["Package", "Version"]
                        ],
                        info=dict(parts["Component", "Info"]),
                    ),
                )
            case _:
                msg = f"Unknown representation: {rep}"
                raise ValueError(msg)

        return f"navigator.clipboard.writeText({json.dumps(r)})"


def session_info(*, os: bool = True, cpu: bool = False) -> SessionInfo:
    """Print versions of imported packages."""
    pkg2dists = packages_distributions()
    user_globals = vars(sys.modules["__main__"])
    info = _AdditionalInfo(
        **({} if os else dict(os=None)),  # type: ignore[arg-type]
        **({} if cpu else dict(cpu=None)),  # type: ignore[arg-type]
    )
    return SessionInfo(pkg2dists, user_globals, info=info)


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
