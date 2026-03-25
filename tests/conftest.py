"""Shared pytest configuration and fixtures for aifmt tests."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("visual", "Visual output options")
    group.addoption(
        "--visual",
        action="store_true",
        default=False,
        help="Print before/after fixer output for human verification.",
    )


@pytest.fixture
def show_visual(request: pytest.FixtureRequest, capsys: pytest.CaptureFixture[str]):
    """Fixture that conditionally prints before/after fixer output.

    Activated by ``pytest --visual``. Uses ``capsys.disabled()`` so output
    is visible without ``-s``.

    Usage::

        def test_box_preserved(show_visual):
            fixed, changes = fix_boxes(broken, target="github")
            show_visual("box fix", broken, fixed, changes)
            assert fixed == broken
    """
    enabled = request.config.getoption("--visual")

    def _show(
        label: str,
        before: str,
        after: str,
        changes: list[str] | None = None,
    ) -> None:
        if not enabled:
            return
        with capsys.disabled():
            print()
            print("\u2500" * 60)
            print(f"  {label}")
            print("\u2500" * 60)
            print()
            print("INPUT:")
            print(before)
            print()
            print("OUTPUT:")
            print(after)
            if changes:
                print()
                print("CHANGES:")
                for c in changes:
                    print(f"  \u2022 {c}")
            identical = before.strip() == after.strip()
            print()
            if identical:
                print("  \u2714 Preserved (output == input)")
            else:
                print("  \u270e Modified")
            print()

    return _show
