"""Introduction management commands."""

import typer

from cli.client import get_client

app = typer.Typer(help="Manage introductions")


@app.command("list")
def list_intros():
    """List incoming and outgoing introductions."""
    client = get_client()
    response = client.get("/introductions")
    data = response.json()

    incoming = data.get("incoming", [])
    outgoing = data.get("outgoing", [])

    if incoming:
        typer.echo("Incoming:")
        typer.echo(f"  {'ID':<38} {'Status':<12} {'Created'}")
        typer.echo("  " + "-" * 70)
        for i in incoming:
            typer.echo(f"  {i['id']:<38} {i['status']:<12} {i['created_at'][:10]}")
    else:
        typer.echo("No incoming introductions.")

    typer.echo()

    if outgoing:
        typer.echo("Outgoing:")
        typer.echo(f"  {'ID':<38} {'Status':<12} {'Created'}")
        typer.echo("  " + "-" * 70)
        for o in outgoing:
            typer.echo(f"  {o['id']:<38} {o['status']:<12} {o['created_at'][:10]}")
    else:
        typer.echo("No outgoing introductions.")


@app.command()
def accept(introduction_id: str = typer.Argument(..., help="Introduction UUID")):
    """Accept an incoming introduction."""
    client = get_client()
    response = client.patch(
        f"/introductions/{introduction_id}",
        json={"status": "accepted"},
    )
    data = response.json()
    typer.echo(f"Introduction accepted: {data['id']}")
    if data.get("requester_contact_info"):
        typer.echo(f"Requester contact info: {data['requester_contact_info']}")
    if data.get("target_contact_info"):
        typer.echo(f"Your contact info shared: {data['target_contact_info']}")


@app.command()
def decline(introduction_id: str = typer.Argument(..., help="Introduction UUID")):
    """Decline an incoming introduction."""
    client = get_client()
    response = client.patch(
        f"/introductions/{introduction_id}",
        json={"status": "declined"},
    )
    typer.echo(f"Introduction declined: {response.json()['id']}")
