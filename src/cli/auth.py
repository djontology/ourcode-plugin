"""Authentication commands: login, status, logout."""

import os
import sys
import time
import webbrowser

import httpx
import typer

from cli.client import CONFIG_PATH, DEFAULT_API_URL, load_config, save_config

app = typer.Typer(help="Authenticate with OurCode")


def _api_base() -> str:
    return os.environ.get("OURCODE_API_URL", DEFAULT_API_URL).rstrip("/")


@app.command()
def login(force: bool = typer.Option(False, "--force", help="Re-authenticate even if already logged in")):
    """Log in to OurCode via GitHub OAuth."""
    if not force:
        config = load_config()
        if config.get("OURCODE_API_TOKEN"):
            typer.echo("Already logged in. Use --force to re-authenticate.")
            return

    base = _api_base()

    try:
        response = httpx.post(f"{base}/api/auth/sessions", timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as e:
        typer.echo(f"Cannot reach the OurCode server: {e}", err=True)
        raise typer.Exit(code=1)

    data = response.json()
    session_id = data["session_id"]
    auth_url = data["auth_url"]

    typer.echo("Opening your browser to sign in with GitHub...")
    webbrowser.open(auth_url)

    typer.echo("Waiting for authentication...")
    for _ in range(150):
        time.sleep(2)
        try:
            poll = httpx.get(f"{base}/api/auth/sessions/{session_id}", timeout=30.0)
            poll.raise_for_status()
        except httpx.HTTPError:
            continue

        poll_data = poll.json()
        status = poll_data.get("status")

        if status == "complete":
            token = poll_data["api_token"]
            save_config(token, base)
            typer.echo("Logged in successfully.")
            return
        if status == "expired":
            typer.echo("Session expired. Please try again.", err=True)
            raise typer.Exit(code=1)

    typer.echo("Timed out waiting for authentication. Please try again.", err=True)
    raise typer.Exit(code=1)


@app.command()
def status():
    """Check login status."""
    config = load_config()
    token = config.get("OURCODE_API_TOKEN")
    if not token:
        typer.echo("Not logged in.")
        raise typer.Exit(code=1)

    base = config.get("OURCODE_API_URL", DEFAULT_API_URL).rstrip("/")
    try:
        response = httpx.get(
            f"{base}/api/developers/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )
    except httpx.HTTPError as e:
        typer.echo(f"Cannot reach the OurCode server: {e}", err=True)
        raise typer.Exit(code=1)

    if response.status_code == 401:
        typer.echo("Token expired or invalid. Run `ourcode auth login --force` to re-authenticate.", err=True)
        raise typer.Exit(code=1)

    response.raise_for_status()
    data = response.json()
    project_count = data.get("project_count", 0)
    typer.echo(f"Logged in. Projects: {project_count}")


@app.command()
def logout():
    """Log out by removing saved credentials."""
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
    typer.echo("Logged out.")
