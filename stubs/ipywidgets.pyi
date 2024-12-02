# SPDX-License-Identifier: MPL-2.0
from collections.abc import Callable, Container, Sequence
from contextlib import AbstractContextManager
from dataclasses import KW_ONLY, dataclass
from types import TracebackType
from typing import Any, Generic, Literal, TypeAlias, TypedDict, TypeVar

_CssProperties: TypeAlias = Literal["inherit", "initial", "unset"]

class Widget:
    def _repr_mimebundle_(
        self,
        include: Container[str] | None = None,
        exclude: Container[str] | None = None,
        **kwargs: object,
    ) -> dict[str, Any]: ...

@dataclass
class Layout(Widget):
    _: KW_ONLY
    align_content: (
        Literal[
            "flex-start",
            "flex-end",
            "center",
            "space-between",
            "space-around",
            "space-evenly",
            "stretch",
        ]
        | _CssProperties
        | None
    ) = None
    align_items: (
        Literal[
            "flex-start",
            "flex-end",
            "center",
            "baseline",
            "stretch",
        ]
        | _CssProperties
        | None
    ) = None
    align_self: (
        Literal[
            "auto",
            "flex-start",
            "flex-end",
            "center",
            "baseline",
            "stretch",
        ]
        | _CssProperties
        | None
    ) = None
    border_top: str | None = None
    border_right: str | None = None
    border_bottom: str | None = None
    border_left: str | None = None
    bottom: str | None = None
    display: str | None = None
    flex: str | None = None
    flex_flow: str | None = None
    height: str | None = None
    justify_content: (
        Literal[
            "flex-start",
            "flex-end",
            "center",
            "space-between",
            "space-around",
        ]
        | _CssProperties
        | None
    ) = None
    justify_items: (
        Literal[
            "flex-start",
            "flex-end",
            "center",
        ]
        | _CssProperties
        | None
    ) = None
    left: str | None = None
    margin: str | None = None
    max_height: str | None = None
    max_width: str | None = None
    min_height: str | None = None
    min_width: str | None = None
    overflow: str | None = None
    order: str | None = None
    padding: str | None = None
    right: str | None = None
    top: str | None = None
    visibility: Literal["visible", "hidden"] | _CssProperties | None = None
    width: str | None = None

    object_fit: (
        Literal[
            "contain",
            "cover",
            "fill",
            "scale-down",
            "none",
        ]
        | _CssProperties
        | None
    ) = None
    object_position: str | None = None

    grid_auto_columns: str | None = None
    grid_auto_flow: (
        Literal[
            "column",
            "row",
            "row dense",
            "column dense",
        ]
        | _CssProperties
        | None
    ) = None
    grid_auto_rows: str | None = None
    grid_gap: str | None = None
    grid_template_rows: str | None = None
    grid_template_columns: str | None = None
    grid_template_areas: str | None = None
    grid_row: str | None = None
    grid_column: str | None = None
    grid_area: str | None = None

@dataclass
class DOMWidget(Widget):
    _: KW_ONLY
    tabbable: bool | None = None
    tooltip: str | None = None
    layout: Layout | dict[str, Any] | None = None

@dataclass
class Box(DOMWidget):
    children: Sequence[Widget]
    _: KW_ONLY
    box_style: Literal["success", "info", "warning", "danger", ""] = ...

class HBox(Box): ...
class VBox(Box): ...

@dataclass
class Accordion(Box):
    children: Sequence[Widget]
    _: KW_ONLY
    titles: Sequence[str] = ()

@dataclass
class Button(DOMWidget):
    _: KW_ONLY
    description: str
    disabled: bool = False
    icon: str = ""
    button_style: Literal[
        "primary",
        "success",
        "info",
        "warning",
        "danger",
        "",
    ] = ""

    def on_click(self, callback: Callable[[Button], None]) -> None: ...

class DescriptionStyle(TypedDict, total=False):
    description_width: str

class _StringStyle(DescriptionStyle, TypedDict, total=False):
    background: str | None
    font_size: str | None
    # text_color: Color | None  # noqa: ERA001

class LabelStyle(_StringStyle, TypedDict, total=False):
    font_family: str | None
    font_style: str | None
    font_variant: str | None
    font_weight: str | None
    text_decoration: str | None

_StringStyleBound = TypeVar("_StringStyleBound", bound=_StringStyle)

@dataclass
class String(Widget, Generic[_StringStyleBound]):
    value: str
    _: KW_ONLY
    placeholder: str = ...
    style: _StringStyleBound = ...

class HTML(String[_StringStyle]): ...
class HTMLMath(String[_StringStyle]): ...
class Label(String[LabelStyle]): ...

_F = TypeVar("_F", bound=Callable[..., Any])

@dataclass
class Output(DOMWidget, AbstractContextManager[None]):
    _: KW_ONLY
    msg_id: str = ""
    outputs: tuple[dict[str, Any], ...] = ()

    def clear_output(self, wait: bool = False) -> None: ...
    def capture(
        self,
        clear_output: bool = False,
        wait: bool = False,
    ) -> Callable[[_F], _F]: ...
    def __enter__(self) -> None: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    def append_stdout(self, text: str) -> None: ...
    def append_stderr(self, text: str) -> None: ...
    def append_display_data(self, display_object: object) -> None: ...
