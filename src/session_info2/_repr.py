from __future__ import annotations

import json
import traceback
from textwrap import dedent, indent
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Callable, Container, Iterable, Mapping

    from . import SessionInfo, _TableHeader

    MimeWidget = Literal["application/vnd.jupyter.widget-view+json"]

    SupportedMime: TypeAlias = Literal[
        "text/plain",
        "text/markdown",
        "text/html",
        "application/json",
        MimeWidget,
    ]

MIME_WIDGET: MimeWidget = "application/vnd.jupyter.widget-view+json"


def repr_markdown(si: SessionInfo) -> str:
    """Generate Markdown representation."""
    # no extra lines possible in markdown tables, so do multiple tables
    return "\n\n".join(
        part
        for header, rows in si._table_parts().items()  # noqa: SLF001
        if (part := _fmt_markdown(header, rows))
    )


def _fmt_markdown(header: _TableHeader, rows: Iterable[tuple[str, str]]) -> str:
    rows = list(rows)
    if not rows:
        return ""
    widths = [max(len(e) for e in col) for col in zip(*(header, *rows), strict=True)]
    row_template = "| " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"
    sep = row_template.format(*(("-" * w) for w in widths))
    rows_fmt = "\n".join(row_template.format(*row) for row in rows)
    return f"{row_template.format(*header)}\n{sep}\n{rows_fmt}"


def repr_html(si: SessionInfo, *, add_details: bool = True) -> str:
    """Generate static HTML representation."""
    parts = "\n".join(
        part
        for header, rows in si._table_parts().items()  # noqa: SLF001
        if (part := _fmt_html(header, rows))
    )
    table = dedent(
        f"""
        <div style="max-height: min(500px, 80vh); overflow-y: auto;">
            <table class=table>
            {indent(parts, " " * 8)}
            </table>
        </div>
        """,
    ).strip()
    if not add_details:
        return table
    return dedent(
        f"""
        {table}
        <details>
            <summary>Copyable Markdown</summary>
            <pre>{repr_markdown(si)}</pre>
        </details>
        """,
    ).strip()


def _fmt_html(header: _TableHeader, rows: Iterable[tuple[str, str]]) -> str:
    def strengthen(k: str) -> str:
        return f"<strong>{k}</strong>" if header[0] == "Package" else k

    trs = "\n".join(
        f"    <tr><td>{strengthen(k)}</td><td>{v}</td></tr>" for k, v in rows
    )
    if not trs:
        return ""
    th = f"    <tr><th>{header[0]}</th><th>{header[1]}</th></tr>"
    bg = "var(--jp-layout-color0, var(--vscode-editor-background, white))"
    style = f' style="position: sticky; top: 0; background-color: {bg};"'
    return f"<thead{style}>\n{th}\n</thead>\n<tbody>\n{trs}\n</tbody>"


def repr_json(si: SessionInfo) -> str:
    parts = si._table_parts()  # noqa: SLF001
    return json.dumps(
        dict(
            packages=_repr_json_part(parts["Package", "Version"]),
            **(
                dict(dependencies=_repr_json_part(parts["Dependency", "Version"]))
                if ("Dependency", "Version") in parts
                else {}
            ),
            info=dict(parts["Component", "Info"]),
        ),
    )


def _repr_json_part(rows: Iterable[tuple[str, str]]) -> list[dict[str, str]]:
    return [dict(package=k, version=v) for k, v in rows]


def repr_widget(si: SessionInfo) -> dict[str, str]:
    widget_bundle = si.widget()._repr_mimebundle_()
    return widget_bundle[MIME_WIDGET]  # type: ignore[no-any-return]


MIME_REPRS: Mapping[SupportedMime, Callable[[SessionInfo], Any]] = MappingProxyType(
    {
        "text/plain": repr,
        "text/markdown": repr_markdown,
        "text/html": repr_html,
        "application/json": repr_json,
        MIME_WIDGET: repr_widget,
    }
)


def repr_mimebundle(
    si: SessionInfo,
    include: Container[str] | None = None,
    exclude: Container[str] | None = None,
    **_kwargs: object,
) -> dict[SupportedMime, Any]:
    mb: dict[SupportedMime, Any] = {}
    for mime, repr_fn in MIME_REPRS.items():
        if include is not None and mime not in include:
            continue
        if exclude is not None and mime in exclude:
            continue
        try:
            mb[mime] = repr_fn(si)
        except ImportError:
            traceback.print_exc()
    return mb
