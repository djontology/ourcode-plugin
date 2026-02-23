"""Tests for cli.auth: login, status, logout commands."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from typer.testing import CliRunner

from cli.auth import app
from cli.client import load_config

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolate_config(tmp_path, monkeypatch):
    """Point CONFIG_PATH at a temp directory for all tests."""
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)
    monkeypatch.setattr("cli.auth.CONFIG_PATH", config_file)


# -- login: already logged in -------------------------------------------------


def test_login_already_logged_in(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)
    monkeypatch.setattr("cli.auth.CONFIG_PATH", config_file)
    config_file.write_text("OURCODE_API_TOKEN=existing\n")

    result = runner.invoke(app, ["login"])
    assert result.exit_code == 0
    assert "Already logged in" in result.output


def test_login_force_bypasses_existing_token(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)
    monkeypatch.setattr("cli.auth.CONFIG_PATH", config_file)
    config_file.write_text("OURCODE_API_TOKEN=existing\n")

    session_resp = MagicMock()
    session_resp.json.return_value = {"session_id": "s1", "auth_url": "https://auth"}
    session_resp.raise_for_status = MagicMock()

    poll_resp = MagicMock()
    poll_resp.json.return_value = {"status": "complete", "api_token": "newtok"}
    poll_resp.raise_for_status = MagicMock()

    with (
        patch("cli.auth.httpx.post", return_value=session_resp),
        patch("cli.auth.httpx.get", return_value=poll_resp),
        patch("cli.auth.webbrowser.open"),
        patch("cli.auth.time.sleep"),
    ):
        result = runner.invoke(app, ["login", "--force"])

    assert result.exit_code == 0
    assert "Logged in successfully" in result.output
    config = load_config()
    assert config["OURCODE_API_TOKEN"] == "newtok"


# -- login: happy path --------------------------------------------------------


def test_login_happy_path(monkeypatch):
    session_resp = MagicMock()
    session_resp.json.return_value = {"session_id": "s1", "auth_url": "https://auth"}
    session_resp.raise_for_status = MagicMock()

    poll_resp = MagicMock()
    poll_resp.json.return_value = {"status": "complete", "api_token": "tok456"}
    poll_resp.raise_for_status = MagicMock()

    with (
        patch("cli.auth.httpx.post", return_value=session_resp),
        patch("cli.auth.httpx.get", return_value=poll_resp),
        patch("cli.auth.webbrowser.open") as mock_browser,
        patch("cli.auth.time.sleep"),
    ):
        result = runner.invoke(app, ["login"])

    assert result.exit_code == 0
    assert "Logged in successfully" in result.output
    mock_browser.assert_called_once_with("https://auth")
    config = load_config()
    assert config["OURCODE_API_TOKEN"] == "tok456"


# -- login: error paths -------------------------------------------------------


def test_login_server_unreachable():
    with patch("cli.auth.httpx.post", side_effect=httpx.ConnectError("fail")):
        result = runner.invoke(app, ["login"])

    assert result.exit_code == 1
    assert "Cannot reach" in result.output


def test_login_session_expired():
    session_resp = MagicMock()
    session_resp.json.return_value = {"session_id": "s1", "auth_url": "https://auth"}
    session_resp.raise_for_status = MagicMock()

    poll_resp = MagicMock()
    poll_resp.json.return_value = {"status": "expired"}
    poll_resp.raise_for_status = MagicMock()

    with (
        patch("cli.auth.httpx.post", return_value=session_resp),
        patch("cli.auth.httpx.get", return_value=poll_resp),
        patch("cli.auth.webbrowser.open"),
        patch("cli.auth.time.sleep"),
    ):
        result = runner.invoke(app, ["login"])

    assert result.exit_code == 1
    assert "expired" in result.output.lower()


def test_login_timeout():
    session_resp = MagicMock()
    session_resp.json.return_value = {"session_id": "s1", "auth_url": "https://auth"}
    session_resp.raise_for_status = MagicMock()

    poll_resp = MagicMock()
    poll_resp.json.return_value = {"status": "pending"}
    poll_resp.raise_for_status = MagicMock()

    with (
        patch("cli.auth.httpx.post", return_value=session_resp),
        patch("cli.auth.httpx.get", return_value=poll_resp),
        patch("cli.auth.webbrowser.open"),
        patch("cli.auth.time.sleep"),
    ):
        result = runner.invoke(app, ["login"])

    assert result.exit_code == 1
    assert "Timed out" in result.output


# -- status --------------------------------------------------------------------


def test_status_no_token():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "Not logged in" in result.output


def test_status_valid_token(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)
    monkeypatch.setattr("cli.auth.CONFIG_PATH", config_file)
    config_file.write_text("OURCODE_API_TOKEN=tok\nOURCODE_API_URL=https://example.com\n")

    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"project_count": 3}
    resp.raise_for_status = MagicMock()

    with patch("cli.auth.httpx.get", return_value=resp):
        result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "Projects: 3" in result.output


def test_status_401_expired(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)
    monkeypatch.setattr("cli.auth.CONFIG_PATH", config_file)
    config_file.write_text("OURCODE_API_TOKEN=tok\nOURCODE_API_URL=https://example.com\n")

    resp = MagicMock()
    resp.status_code = 401

    with patch("cli.auth.httpx.get", return_value=resp):
        result = runner.invoke(app, ["status"])

    assert result.exit_code == 1
    assert "expired or invalid" in result.output.lower()


# -- logout --------------------------------------------------------------------


def test_logout_removes_config(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)
    monkeypatch.setattr("cli.auth.CONFIG_PATH", config_file)
    config_file.write_text("OURCODE_API_TOKEN=tok\n")

    result = runner.invoke(app, ["logout"])
    assert result.exit_code == 0
    assert "Logged out" in result.output
    assert not config_file.exists()


def test_logout_no_config_file():
    result = runner.invoke(app, ["logout"])
    assert result.exit_code == 0
    assert "Logged out" in result.output
