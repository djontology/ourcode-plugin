"""Profile management commands."""

import typer

from cli.client import get_client

app = typer.Typer(help="Manage your developer profile")


@app.command()
def show():
    """Show your profile."""
    client = get_client()
    response = client.get("/developers/me")
    data = response.json()
    typer.echo(f"Contact info set: {data['has_contact_info']}")
    typer.echo(f"Projects: {data['project_count']}")


@app.command("set-contact")
def set_contact(contact_info: str = typer.Argument(..., help="Free-text contact info")):
    """Set or update your contact info."""
    client = get_client()
    response = client.post(
        "/developers/me/contact-info",
        json={"contact_info": contact_info},
    )
    data = response.json()
    typer.echo(f"Contact info set: {data['contact_info']}")


@app.command()
def delete():
    """Delete your account and all data."""
    typer.confirm("This will permanently delete your account and all data. Continue?", abort=True)
    client = get_client()
    client.delete("/developers/me")
    typer.echo("Account deleted.")
