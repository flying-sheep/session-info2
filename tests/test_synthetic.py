"""Run tests with artificial data."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import pytest

from session_info2 import SessionInfo, _repr

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.parametrize(
    ("pkg2dists", "imports", "expected"),
    [
        pytest.param({}, {}, "", id="empty"),
        pytest.param(dict(basic=["basic"]), ["basic"], "basic\t1.0", id="package"),
        pytest.param(dict(basic=["basic"]), ["basic:fn"], "basic\t1.0", id="function"),
        pytest.param(dict(basic=["basic"]), ["basic:Cls"], "basic\t1.0", id="class"),
        pytest.param(
            dict(namespace=["namespace.package"]),
            ["namespace.package"],
            "namespace.package\t2.2.1",
            id="namespace_package",
        ),
        pytest.param(
            dict(mis_match=["mismatch"]),
            ["mis_match"],
            "mismatch\t1.1 (1.1.post0.dev0)",
            id="mismatch",
        ),
    ],
)
def test_repr(
    import_path: Callable[[str], Any],
    pkg2dists: dict[str, list[str]],
    imports: list[str],
    expected: str,
) -> None:
    user_globals = {re.split(r"[.:]", p)[-1]: import_path(p) for p in imports}
    si = SessionInfo(pkg2dists, user_globals)
    r = repr(si)
    pkgs, info = r.split("\n----\t----\n") if "----" in r else ("", r)
    assert pkgs == expected
    assert re.fullmatch(
        "Python\t[^\n]+\nOS\t[^\n]+\nCPU\t[^\n]+\nUpdated\t[^\n]+", info, re.MULTILINE
    )


@pytest.mark.parametrize(
    ("pkg2dists", "imports", "pkgs_expected"),
    [
        pytest.param({}, {}, [], id="empty"),
        pytest.param(
            dict(basic=["basic"]),
            ["basic"],
            ["| basic   | 1.0     |"],
            id="package",
        ),
        pytest.param(
            dict(basic=["basic"]),
            ["basic:fn"],
            ["| basic   | 1.0     |"],
            id="function",
        ),
        # no need to test class again
    ],
)
@pytest.mark.parametrize(
    ("dep2dists", "deps_expected"),
    [
        pytest.param({}, [], id="no_deps"),
        pytest.param(dict(dep=["dep"]), ["| dep        | 0.3     |"], id="with_dep"),
    ],
)
def test_markdown(
    *,
    import_path: Callable[[str], Any],
    pkg2dists: dict[str, list[str]],
    dep2dists: dict[str, list[str]],
    imports: list[str],
    pkgs_expected: list[str],
    deps_expected: list[str],
) -> None:
    user_globals = {re.split(r"[.:]", p)[-1]: import_path(p) for p in imports}

    si = SessionInfo(pkg2dists | dep2dists, user_globals)
    parts = _repr.repr_markdown(si).split("\n\n")
    pkg_str: str | None
    dep_str: str | None
    info_str: str
    if len(parts) == 3:  # noqa: PLR2004
        pkg_str, dep_str, info_str = parts
    elif len(parts) == 1:
        [info_str] = parts
        pkg_str = dep_str = None
    elif "Package" in parts[0]:
        pkg_str, info_str = parts
        dep_str = None
    elif "Dependency" in parts[0]:
        dep_str, info_str = parts
        pkg_str = None
    else:
        pytest.fail("Unexpected output")

    for name, s, name2dists, expected in [
        ("Package", pkg_str, pkg2dists, pkgs_expected),
        ("Dependency", dep_str, dep2dists, deps_expected),
    ]:
        if s is None:
            continue
        header, sep, *rows = s.splitlines()
        if name2dists:
            [[pkg_name]] = name2dists.values()
            n_extra = len(pkg_name) - len(name)
        else:
            n_extra = 0
        assert header == f"| {name}{' ' * n_extra} | Version |"
        assert sep == f"| {'-' * len(name)}{'-' * n_extra} | ------- |"
        assert rows == expected

    info_header, info_sep, *info_rows = info_str.splitlines()
    info_extra = max(len(r.split("|")[2].strip()) for r in info_rows) - len("Info")
    assert info_header == f"| Component | Info{' ' * info_extra} |"
    assert info_sep == f"| --------- | ----{'-' * info_extra} |"
    # info_rows content is already tested for plain text, no need to test it again
