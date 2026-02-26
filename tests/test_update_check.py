"""Tests for cli.update_check: background version check with caching."""

import json
import sys
import time

import pytest

from cli import update_check


@pytest.fixture(autouse=True)
def _isolate_cache(tmp_path, monkeypatch):
    """Point CACHE_PATH at a temp directory so tests never touch ~/.ourcode."""
    cache_file = tmp_path / "update-check"
    monkeypatch.setattr("cli.update_check.CACHE_PATH", cache_file)


@pytest.fixture()
def cache_file(tmp_path):
    return tmp_path / "update-check"


# -- _fetch_latest_version -----------------------------------------------------


def test_fetch_latest_version_parses_pypi_json(monkeypatch):
    """Should extract version from PyPI JSON API response."""

    def fake_get(url, **kwargs):
        class Resp:
            status_code = 200

            def json(self):
                return {"info": {"version": "1.2.3"}}

            def raise_for_status(self):
                pass

        return Resp()

    monkeypatch.setattr("httpx.get", fake_get)
    assert update_check._fetch_latest_version() == "1.2.3"


def test_fetch_latest_version_returns_none_on_network_error(monkeypatch):
    """Network failures should return None, never raise."""

    def fake_get(url, **kwargs):
        raise Exception("network down")

    monkeypatch.setattr("httpx.get", fake_get)
    assert update_check._fetch_latest_version() is None


# -- _read_cache / _write_cache ------------------------------------------------


def test_cache_roundtrip(cache_file):
    update_check._write_cache("2.0.0")
    version, ts = update_check._read_cache()
    assert version == "2.0.0"
    assert time.time() - ts < 5


def test_read_cache_returns_none_when_missing():
    version, ts = update_check._read_cache()
    assert version is None
    assert ts == 0.0


def test_read_cache_returns_none_on_corrupt_file(cache_file):
    cache_file.write_text("not json")
    version, ts = update_check._read_cache()
    assert version is None
    assert ts == 0.0


# -- check_for_update (synchronous core) --------------------------------------


def test_check_for_update_prints_notice_when_outdated(monkeypatch, capsys):
    """Should print to stderr when a newer version is available."""
    monkeypatch.setattr("cli.update_check._fetch_latest_version", lambda: "9.9.9")
    monkeypatch.setattr("cli.update_check._get_current_version", lambda: "0.1.0")

    update_check._check_for_update()

    captured = capsys.readouterr()
    assert "9.9.9" in captured.err
    assert "uv tool upgrade ourcode" in captured.err


def test_check_for_update_silent_when_up_to_date(monkeypatch, capsys):
    """Should print nothing when already on the latest version."""
    monkeypatch.setattr("cli.update_check._fetch_latest_version", lambda: "0.3.0")
    monkeypatch.setattr("cli.update_check._get_current_version", lambda: "0.3.0")

    update_check._check_for_update()

    captured = capsys.readouterr()
    assert captured.err == ""


def test_check_for_update_silent_on_fetch_failure(monkeypatch, capsys):
    """Should print nothing when the version check fails."""
    monkeypatch.setattr("cli.update_check._fetch_latest_version", lambda: None)

    update_check._check_for_update()

    captured = capsys.readouterr()
    assert captured.err == ""


def test_check_for_update_uses_cache_within_24h(monkeypatch, cache_file, capsys):
    """Should not fetch if cache is fresh."""
    # Write a fresh cache saying we're up to date
    update_check._write_cache("0.3.0")
    monkeypatch.setattr("cli.update_check._get_current_version", lambda: "0.3.0")

    fetch_called = False
    original_fetch = update_check._fetch_latest_version

    def spy():
        nonlocal fetch_called
        fetch_called = True
        return original_fetch()

    monkeypatch.setattr("cli.update_check._fetch_latest_version", spy)

    update_check._check_for_update()

    assert not fetch_called


def test_check_for_update_fetches_when_cache_stale(monkeypatch, cache_file, capsys):
    """Should re-fetch if cache is older than 24h."""
    # Write a stale cache
    data = {"latest_version": "0.2.0", "checked_at": time.time() - 90000}
    cache_file.write_text(json.dumps(data))
    monkeypatch.setattr("cli.update_check._get_current_version", lambda: "0.3.0")
    monkeypatch.setattr("cli.update_check._fetch_latest_version", lambda: "0.3.0")

    update_check._check_for_update()

    # Cache should be updated
    version, ts = update_check._read_cache()
    assert version == "0.3.0"


# -- env var / flag opt-out ---------------------------------------------------


def test_env_var_disables_check(monkeypatch, capsys):
    """OURCODE_NO_UPDATE_CHECK=1 should skip the check entirely."""
    monkeypatch.setenv("OURCODE_NO_UPDATE_CHECK", "1")

    fetch_called = False

    def spy():
        nonlocal fetch_called
        fetch_called = True

    monkeypatch.setattr("cli.update_check._fetch_latest_version", spy)

    update_check._check_for_update()

    assert not fetch_called
    assert capsys.readouterr().err == ""
