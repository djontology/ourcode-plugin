"""Tests for cli.client: config persistence and APIClient construction."""

import pytest

from cli.client import APIClient, get_client, load_config, save_config


@pytest.fixture(autouse=True)
def _isolate_config(tmp_path, monkeypatch):
    """Point CONFIG_PATH at a temp directory so tests never touch ~/.ourcode."""
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)


# -- save_config / load_config ------------------------------------------------


def test_config_roundtrip(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)

    save_config("tok123", "https://example.com")
    result = load_config()

    assert result["OURCODE_API_TOKEN"] == "tok123"
    assert result["OURCODE_API_URL"] == "https://example.com"


def test_load_config_missing_file():
    result = load_config()
    assert result == {}


def test_load_config_ignores_comments_and_blanks(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)
    config_file.write_text("# a comment\n\nOURCODE_API_TOKEN=abc\n\n")

    result = load_config()
    assert result == {"OURCODE_API_TOKEN": "abc"}


# -- APIClient -----------------------------------------------------------------


def test_api_client_raises_without_token():
    with pytest.raises(ValueError, match="no API token"):
        APIClient()


def test_api_client_constructs_url_and_header(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    monkeypatch.setattr("cli.client.CONFIG_PATH", config_file)
    save_config("mytoken", "https://example.com")

    client = APIClient()
    assert client.base_url == "https://example.com/api"
    assert client.token == "mytoken"
    assert client._client.headers["authorization"] == "Bearer mytoken"


# -- get_client ----------------------------------------------------------------


def test_get_client_exits_when_no_token():
    from typer import Exit

    with pytest.raises(Exit):
        get_client()
