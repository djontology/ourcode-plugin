"""Profile management commands."""

import httpx
import typer

from cli.client import get_client

app = typer.Typer(help="Manage your developer profile")

# Client-side validation only — server is the source of truth.
# If the server adds new types, update this tuple to match.
CONTACT_TYPES = ("email", "discord", "linkedin", "slack", "twitter", "github_discussion", "other")


def _parse_method(entry: str) -> dict:
    """Parse a 'type:value' string into a contact method dict."""
    if ":" not in entry:
        typer.echo(f"Invalid method format '{entry}'. Use type:value (e.g. email:you@example.com)", err=True)
        raise typer.Exit(code=1)
    ctype, value = entry.split(":", 1)
    ctype = ctype.strip().lower()
    value = value.strip()
    if ctype not in CONTACT_TYPES:
        typer.echo(f"Unknown contact type '{ctype}'. Valid types: {', '.join(CONTACT_TYPES)}", err=True)
        raise typer.Exit(code=1)
    return {"type": ctype, "value": value}


def _fetch_contact_info(client) -> dict | None:
    """Fetch current contact info, returning None if not set."""
    try:
        response = client.get("/developers/me/contact-info")
        return response.json().get("contact_info")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise


def _save_contact_info(client, contact_info: dict) -> dict:
    """POST contact info and return the response data."""
    response = client.post("/developers/me/contact-info", json={"contact_info": contact_info})
    return response.json().get("contact_info", response.json())


def _display_contact_info(data: dict) -> None:
    """Print contact info to stdout."""
    for m in data.get("methods", []):
        pref = " (preferred)" if m.get("preferred") else ""
        typer.echo(f"  {m['type']}: {m['value']}{pref}")
    if data.get("timezone"):
        typer.echo(f"  Timezone: {data['timezone']}")
    if data.get("notes"):
        typer.echo(f"  Notes: {data['notes']}")


@app.command()
def show():
    """Show your profile."""
    client = get_client()
    response = client.get("/developers/me")
    data = response.json()
    typer.echo(f"Contact info set: {data['has_contact_info']}")
    if data.get("contact_method_count"):
        typer.echo(f"Contact methods: {data['contact_method_count']}")
    typer.echo(f"Projects: {data['project_count']}")


@app.command("set-contact")
def set_contact(
    method: list[str] = typer.Option(..., "--method", "-m", help="Contact method as type:value (e.g. email:you@example.com)"),
    preferred: str = typer.Option(..., "--preferred", "-p", help="Contact type to mark as preferred"),
    timezone: str = typer.Option(None, "--timezone", "-t", help="IANA timezone (e.g. America/New_York)"),
    notes: str = typer.Option(None, "--notes", "-n", help="Additional notes (max 500 chars)"),
):
    """Replace all contact info with the provided methods."""
    methods = []
    for entry in method:
        m = _parse_method(entry)
        m["preferred"] = m["type"] == preferred.strip().lower()
        methods.append(m)

    if not any(m["preferred"] for m in methods):
        typer.echo(f"Preferred type '{preferred}' not found in provided methods.", err=True)
        raise typer.Exit(code=1)

    contact_info: dict = {"methods": methods}
    if timezone:
        contact_info["timezone"] = timezone
    if notes:
        contact_info["notes"] = notes

    client = get_client()
    data = _save_contact_info(client, contact_info)

    typer.echo("Contact info updated:")
    _display_contact_info(data)


@app.command("add-contact")
def add_contact(
    method: str = typer.Argument(..., help="Contact method as type:value (e.g. linkedin:testerson)"),
    preferred: bool = typer.Option(False, "--preferred", "-p", help="Mark this method as preferred"),
):
    """Add a contact method to your existing contact info."""
    parsed = _parse_method(method)
    client = get_client()
    existing = _fetch_contact_info(client)

    if existing is None:
        # No contact info yet — this becomes the only (and preferred) method
        parsed["preferred"] = True
        data = _save_contact_info(client, {"methods": [parsed]})
        typer.echo("Contact info created:")
        _display_contact_info(data)
        return

    methods = existing.get("methods", [])

    # Replace if same type already exists, otherwise append
    replaced = False
    for i, m in enumerate(methods):
        if m["type"] == parsed["type"]:
            methods[i] = {**m, "value": parsed["value"]}
            replaced = True
            break
    if not replaced:
        parsed["preferred"] = False
        methods.append(parsed)

    if preferred:
        for m in methods:
            m["preferred"] = m["type"] == parsed["type"]

    existing["methods"] = methods
    data = _save_contact_info(client, existing)
    typer.echo("Contact info updated:")
    _display_contact_info(data)


@app.command("remove-contact")
def remove_contact(
    contact_type: str = typer.Argument(..., help="Contact type to remove (e.g. linkedin)"),
):
    """Remove a contact method by type."""
    contact_type = contact_type.strip().lower()
    client = get_client()
    existing = _fetch_contact_info(client)

    if existing is None:
        typer.echo("No contact info set.", err=True)
        raise typer.Exit(code=1)

    methods = existing.get("methods", [])
    remaining = [m for m in methods if m["type"] != contact_type]

    if len(remaining) == len(methods):
        typer.echo(f"No contact method of type '{contact_type}' found.", err=True)
        raise typer.Exit(code=1)

    if not remaining:
        typer.echo("Cannot remove the last contact method. Use set-contact to replace it instead.", err=True)
        raise typer.Exit(code=1)

    # If we removed the preferred method, make the first remaining one preferred
    if not any(m.get("preferred") for m in remaining):
        remaining[0]["preferred"] = True

    existing["methods"] = remaining
    data = _save_contact_info(client, existing)
    typer.echo(f"Removed {contact_type}. Current contact info:")
    _display_contact_info(data)


@app.command()
def delete():
    """Delete your account and all data."""
    typer.confirm("This will permanently delete your account and all data. Continue?", abort=True)
    client = get_client()
    client.delete("/developers/me")
    typer.echo("Account deleted.")
