import builtins
from unittest.mock import patch

import pytest

from kiteconnect import cli


def test_cli_login(capsys):
    """Ensure login command prints access token."""
    with patch("kiteconnect.connect.KiteConnect.generate_session", return_value={"access_token": "xyz"}):
        cli.main([
            "login",
            "--api-key", "kite",
            "--api-secret", "secret",
            "--request-token", "req",
        ])
    out = capsys.readouterr().out.strip()
    assert out == "xyz"
