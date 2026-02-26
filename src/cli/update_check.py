"""Background update check for the OurCode CLI.

Checks TestPyPI for a newer version at most once every 24 hours.
Caches the result in ~/.ourcode/update-check. Prints a one-line
stderr notice if an update is available.

Disable via --no-update-check flag or OURCODE_NO_UPDATE_CHECK=1.
"""

import json
import os
import sys
import threading
import time
from importlib.metadata import version as pkg_version
from pathlib import Path

import httpx

CACHE_PATH = Path.home() / ".ourcode" / "update-check"
CHECK_INTERVAL = 86400  # 24 hours
PYPI_URL = "https://test.pypi.org/pypi/ourcode/json"


def _get_current_version() -> str:
    return pkg_version("ourcode")


def _fetch_latest_version() -> str | None:
    """Query the package index for the latest version. Returns None on any failure."""
    try:
        resp = httpx.get(PYPI_URL, timeout=5.0)
        resp.raise_for_status()
        return resp.json()["info"]["version"]
    except Exception:
        return None


def _read_cache() -> tuple[str | None, float]:
    """Read cached version info. Returns (version, checked_at) or (None, 0.0)."""
    try:
        data = json.loads(CACHE_PATH.read_text())
        return data["latest_version"], data["checked_at"]
    except Exception:
        return None, 0.0


def _write_cache(latest_version: str) -> None:
    """Write version info to cache file."""
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps({"latest_version": latest_version, "checked_at": time.time()})
        )
    except Exception:
        pass


def _check_for_update() -> None:
    """Core check logic. Runs synchronously — called from background thread or directly."""
    if os.environ.get("OURCODE_NO_UPDATE_CHECK") == "1":
        return

    cached_version, checked_at = _read_cache()

    if time.time() - checked_at < CHECK_INTERVAL:
        # Cache is fresh — use it
        latest = cached_version
    else:
        latest = _fetch_latest_version()
        if latest:
            _write_cache(latest)

    if not latest:
        return

    current = _get_current_version()
    if latest != current and _is_newer(latest, current):
        print(
            f"Update available: {current} \u2192 {latest}. "
            f"Run 'uv tool upgrade ourcode' to update.",
            file=sys.stderr,
        )


def _is_newer(latest: str, current: str) -> bool:
    """Compare version strings. Returns True if latest > current."""
    try:
        from packaging.version import Version

        return Version(latest) > Version(current)
    except ImportError:
        # Fall back to simple tuple comparison
        def _parts(v: str) -> tuple[int, ...]:
            return tuple(int(x) for x in v.split("."))

        try:
            return _parts(latest) > _parts(current)
        except (ValueError, TypeError):
            return False


def start_background_check() -> None:
    """Launch the update check in a daemon thread so it doesn't block CLI startup."""
    if os.environ.get("OURCODE_NO_UPDATE_CHECK") == "1":
        return
    t = threading.Thread(target=_check_for_update, daemon=True)
    t.start()
