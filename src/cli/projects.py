"""Project management commands."""

import json
from pathlib import Path

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
def submit(
    summary_file: str = typer.Argument(
        ".ourcode/summary.json", help="Path to the project summary JSON file"
    ),
    register: bool = typer.Option(True, help="Register project permanently (vs ephemeral 24h)"),
):
    """Submit a project summary for matching."""
    path = Path(summary_file)
    if not path.exists():
        typer.echo(f"Summary file not found: {summary_file}", err=True)
        raise typer.Exit(code=1)

    summary = json.loads(path.read_text())
    client = get_client()
    response = client.post(
        f"/projects?register={str(register).lower()}", json=summary
    )
    data = response.json()

    typer.echo(f"Project ID: {data['id']}")
    typer.echo(f"Status: {'Registered' if data['is_registered'] else 'Ephemeral'}")
    typer.echo(f"Expires: {data.get('expires_at') or 'never'}")

    matches = data.get("matches", [])
    if not matches:
        typer.echo("\nNo similar projects found yet.")
        return

    typer.echo(f"\nFound {len(matches)} similar project(s):\n")

    by_tier: dict[str, list] = {}
    for m in matches:
        by_tier.setdefault(m["tier"], []).append(m)

    tier_labels = {
        "exact": "Exact matches",
        "partial": "Partial matches",
        "related": "Related projects",
    }
    for tier in ("exact", "partial", "related"):
        tier_matches = by_tier.get(tier, [])
        if not tier_matches:
            continue
        typer.echo(f"  {tier_labels.get(tier, tier)}:")
        for m in tier_matches:
            pct = int(m["similarity"] * 100)
            stage = m.get("lifecycle_stage", "unknown")
            goals = "; ".join(m.get("summary", {}).get("project", {}).get("goals", []))
            tech_parts = (
                m.get("summary", {}).get("tech_stack", {}).get("languages", [])
                + m.get("summary", {}).get("tech_stack", {}).get("frameworks", [])
            )
            tech = ", ".join(tech_parts)
            typer.echo(f"    - {pct}% similar ({stage})")
            lt = m.get("listing_type")
            name = m.get("display_name")
            if lt and lt != "private":
                label = f"[{lt.upper()}]"
                if name:
                    label += f" {name}"
                typer.echo(f"      {label}")
            elif name:
                typer.echo(f"      {name}")
            repo_url = m.get("repo_url")
            if repo_url:
                typer.echo(f"      Repo: {repo_url}")
            if goals:
                typer.echo(f"      Goals: {goals}")
            if tech:
                typer.echo(f"      Tech: {tech}")


@app.command()
def delete(project_id: str = typer.Argument(..., help="Project UUID to delete")):
    """Delete a project."""
    typer.confirm(f"Delete project {project_id}?", abort=True)
    client = get_client()
    client.delete(f"/projects/{project_id}")
    typer.echo(f"Project {project_id} deleted.")
