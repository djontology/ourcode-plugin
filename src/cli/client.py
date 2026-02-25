"""API client for the OurCode CLI. Reads config from ~/.ourcode/config."""

from pathlib import Path

import httpx

CONFIG_PATH = Path.home() / ".ourcode" / "config"
DEFAULT_API_URL = "https://api.ourcode.dev"


def save_config(token: str, api_url: str) -> None:
    """Write token and API URL to ~/.ourcode/config."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(f"OURCODE_API_TOKEN={token}\nOURCODE_API_URL={api_url}\n")


def load_config() -> dict[str, str]:
    """Load config from ~/.ourcode/config.

    File format (key=value):
        OURCODE_API_TOKEN=<token>
        OURCODE_API_URL=<url>
    """
    config = {}
    if not CONFIG_PATH.exists():
        return config
    for line in CONFIG_PATH.read_text().strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config


class APIClient:
    """HTTP client for the OurCode API."""

    def __init__(self, token: str | None = None, base_url: str | None = None):
        config = load_config()
        self.token = token or config.get("OURCODE_API_TOKEN", "")
        raw_url = (
            base_url or config.get("OURCODE_API_URL", "https://our-code-production.up.railway.app")
        ).rstrip("/")
        self.base_url = f"{raw_url}/api"

        if not self.token:
            raise ValueError(
                "no API token found. Run the ourcode-login skill first to authenticate."
            )

        # Note: httpx.Client is not explicitly closed. This is intentional because the APIClient
        # is short-lived in CLI commands; process exit closes the connection.
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=30.0,
        )

    def get(self, path: str) -> httpx.Response:
        response = self._client.get(path)
        response.raise_for_status()
        return response

    def post(self, path: str, json: dict | None = None) -> httpx.Response:
        response = self._client.post(path, json=json)
        response.raise_for_status()
        return response

    def patch(self, path: str, json: dict | None = None) -> httpx.Response:
        response = self._client.patch(path, json=json)
        response.raise_for_status()
        return response

    def delete(self, path: str) -> httpx.Response:
        response = self._client.delete(path)
        response.raise_for_status()
        return response


def get_client() -> APIClient:
    """Create an APIClient, exiting with a helpful message if no token is configured.

    All CLI command files import and use this function instead of duplicating
    the try/except error handling in each file.
    """
    import typer

    try:
        return APIClient()
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)


def format_contact_info(info):
    """Format structured or plain-text contact info for display.

    Handles both the new structured format (dict with methods array)
    and the legacy plain string format for backwards compatibility.
    """
    if isinstance(info, str):
        return info
    lines = []
    for m in info.get("methods", []):
        pref = " (preferred)" if m.get("preferred") else ""
        lines.append(f"    {m['type']}: {m['value']}{pref}")
    if info.get("timezone"):
        lines.append(f"    Timezone: {info['timezone']}")
    if info.get("notes"):
        lines.append(f"    Notes: {info['notes']}")
    return "\n".join(lines)
