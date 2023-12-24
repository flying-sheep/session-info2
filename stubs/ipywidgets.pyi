from collections.abc import Callable, Container, Sequence
from typing import Any, Generic, Literal, TypedDict, TypeVar

class Widget:
    def _repr_mimebundle_(
        self,
        include: Container[str] | None = None,
        exclude: Container[str] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any]: ...

class Box(Widget):
    def __init__(
        self,
        children: Sequence[Widget],
        *,
        box_style: Literal["success", "info", "warning", "danger", ""] = "",
    ) -> None: ...

class HBox(Box): ...
class VBox(Box): ...

class Button(Widget):
    def __init__(
        self,
        *,
        description: str,
        disabled: bool = False,
        icon: str = "",
        button_style: Literal[
            "primary",
            "success",
            "info",
            "warning",
            "danger",
            "",
        ] = "",
    ) -> None: ...
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

class String(Widget, Generic[_StringStyleBound]):
    def __init__(
        self,
        value: str,
        *,
        placeholder: str = "\u200b",
        style: _StringStyleBound = ...,
    ) -> None: ...

class HTML(String[_StringStyle]): ...
class HTMLMath(String[_StringStyle]): ...
class Label(String[LabelStyle]): ...
