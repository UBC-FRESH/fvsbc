"""Tests for the ``fresh-fvsbc`` package skeleton.

They check that the package imports, that it carries a version, and that the version agrees with
the one ``pyproject.toml`` declares. The last check is the one worth having: the version lives in
two places, and nothing else notices when they drift apart.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import fresh_fvsbc

ROOT: Path = Path(__file__).resolve().parents[1]


def declared_version() -> str:
    """Return the version that ``pyproject.toml`` declares for the project."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        data: dict[str, Any] = tomllib.load(handle)
    return str(data["project"]["version"])


def test_package_imports_and_carries_a_version() -> None:
    """The package exposes a non-empty version string."""
    assert isinstance(fresh_fvsbc.__version__, str)
    assert fresh_fvsbc.__version__


def test_package_version_matches_pyproject() -> None:
    """The version in the package equals the one that ``pyproject.toml`` declares."""
    assert fresh_fvsbc.__version__ == declared_version()


def test_package_documents_itself() -> None:
    """The package module carries a docstring, which the lint rules require."""
    assert fresh_fvsbc.__doc__


def test_package_exports_only_names_it_defines() -> None:
    """Every name in ``__all__`` exists on the package.

    Sortedness is not asserted here: ruff's ``RUF022`` enforces it in the lint gate, and it has
    fired on this file when names were added out of order. A duplicate is not a defect, but it is a
    smell nothing else checks, so that one is asserted.
    """
    assert all(hasattr(fresh_fvsbc, name) for name in fresh_fvsbc.__all__)
    assert len(set(fresh_fvsbc.__all__)) == len(fresh_fvsbc.__all__)
