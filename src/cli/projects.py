"""Project management commands."""

import typer

from cli.client import get_client

app = typer.Typer(help="Manage your projects")


@app.command("list")
def list_projects():
    """List your projects with match counts."""
    client = get_client()
    response = client.get("/projects")
    data = response.json()
    projects = data.get("projects", [])
    if not projects:
        typer.echo("No projects found.")
        return
    typer.echo(f"{'ID':<38} {'Stage':<12} {'Registered':<12} {'Created'}")
    typer.echo("-" * 80)
    for p in projects:
        typer.echo(
            f"{p['id']:<38} {p['lifecycle_stage']:<12} "
            f"{'yes' if p['is_registered'] else 'no':<12} {p['created_at'][:10]}"
        )


@app.command()
def delete(project_id: str = typer.Argument(..., help="Project UUID to delete")):
    """Delete a project."""
    typer.confirm(f"Delete project {project_id}?", abort=True)
    client = get_client()
    client.delete(f"/projects/{project_id}")
    typer.echo(f"Project {project_id} deleted.")
