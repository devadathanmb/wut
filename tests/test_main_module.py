"""Tests for module entrypoint execution."""

import runpy
from unittest.mock import patch


def test_python_m_entrypoint_calls_main() -> None:
    """Running wut.__main__ as __main__ should invoke CLI main."""
    with patch("wut.cli.main") as mock_main:
        runpy.run_module("wut.__main__", run_name="__main__")

    mock_main.assert_called_once()
