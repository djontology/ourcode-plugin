"""Profile management commands."""

import typer

from cli.client import get_client

app = typer.Typer(help="Manage your developer profile")

# Client-side validation only — server is the source of truth.
# If the server adds new types, update this tuple to match.
CONTACT_TYPES = ("email", "discord", "linkedin", "slack", "twitter", "github_discussion", "other")


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
    """Set or update your contact info with structured methods."""
    methods = []
    for entry in method:
        if ":" not in entry:
            typer.echo(f"Invalid method format '{entry}'. Use type:value (e.g. email:you@example.com)", err=True)
            raise typer.Exit(code=1)
        ctype, value = entry.split(":", 1)
        ctype = ctype.strip().lower()
        value = value.strip()
        if ctype not in CONTACT_TYPES:
            typer.echo(f"Unknown contact type '{ctype}'. Valid types: {', '.join(CONTACT_TYPES)}", err=True)
            raise typer.Exit(code=1)
        methods.append({"type": ctype, "value": value, "preferred": ctype == preferred.strip().lower()})

    if not any(m["preferred"] for m in methods):
        typer.echo(f"Preferred type '{preferred}' not found in provided methods.", err=True)
        raise typer.Exit(code=1)

    payload: dict = {"methods": methods}
    if timezone:
        payload["timezone"] = timezone
    if notes:
        payload["notes"] = notes

    client = get_client()
    response = client.post("/developers/me/contact-info", json=payload)
    data = response.json()

    typer.echo("Contact info updated:")
    for m in data.get("methods", []):
        pref = " (preferred)" if m.get("preferred") else ""
        typer.echo(f"  {m['type']}: {m['value']}{pref}")
    if data.get("timezone"):
        typer.echo(f"  Timezone: {data['timezone']}")
    if data.get("notes"):
        typer.echo(f"  Notes: {data['notes']}")


@app.command()
def delete():
    """Delete your account and all data."""
    typer.confirm("This will permanently delete your account and all data. Continue?", abort=True)
    client = get_client()
    client.delete("/developers/me")
    typer.echo("Account deleted.")
