# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ._repr import MIME_REPRS, repr_html, repr_html_parts

if TYPE_CHECKING:
    from ipywidgets import Widget

    from . import SessionInfo
    from ._repr import SupportedMime


def widget(si: SessionInfo) -> Widget:
    """Generate interactive HTML representation."""
    import ipywidgets as widgets

    try:
        from IPython.display import Javascript  # type: ignore[import-not-found]
    except ImportError:
        return widgets.HTML(value=repr_html(si))

    button = widgets.Button(
        description="Copy as Markdown",
        icon="copy",
        layout=widgets.Layout(width="auto"),
    )
    output = widgets.Output(layout=widgets.Layout(display="none"))
    copy_md = Javascript(_clipboard_js(si, "text/markdown"))

    def on_click(_: widgets.Button) -> None:
        output.clear_output()
        output.append_display_data(copy_md)

    button.on_click(on_click)

    content, deps = repr_html_parts(si)
    w = widgets.VBox((button, output, widgets.HTML(value=content)))
    if not deps:
        return w
    # Maybe: widgets.Accordion(children=[widgets.HTML(deps)], titles=["Dependencies"]),
    return widgets.HBox((w, widgets.HTML(deps)))


def _clipboard_js(
    si: SessionInfo,
    rep: SupportedMime,
) -> str:
    """Javascript to copy representation to clipboard."""
    r = MIME_REPRS[rep](si)
    return f"navigator.clipboard.writeText({json.dumps(r)})"
