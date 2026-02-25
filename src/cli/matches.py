"""Match listing and introduction request commands."""

import typer

from cli.client import get_client

app = typer.Typer(help="View and act on matches")


@app.command("list")
def list_matches(
    project_id: str = typer.Argument(..., help="Project UUID"),
    listing_type: str = typer.Option(None, "--type", help="Filter by listing type (private, public, scraped)"),
):
    """List matches for a project."""
    client = get_client()
    url = f"/projects/{project_id}/matches"
    if listing_type:
        url += f"?listing_type={listing_type}"
    response = client.get(url)
    data = response.json()
    matches = data.get("matches", [])
    if not matches:
        typer.echo("No matches found.")
        return
    typer.echo(f"{'Match ID':<38} {'Type':<10} {'Tier':<10} {'Similarity':<12} {'Status':<12} {'Name'}")
    typer.echo("-" * 100)
    for m in matches:
        lt = m.get("listing_type", "private")
        status = m.get("introduction_status") or "-"
        name = m.get("other_project", {}).get("display_name") or "-"
        typer.echo(
            f"{m['match_id']:<38} {lt:<10} {m['tier']:<10} "
            f"{m['similarity']:<12.4f} {status:<12} {name}"
        )


@app.command()
def show(
    match_id: str = typer.Argument(..., help="Match ID to display"),
    project_id: str = typer.Option(..., "--project", help="Project ID that owns the match"),
):
    """Show detailed comparison for a specific match."""
    client = get_client()
    response = client.get(f"/projects/{project_id}/matches")
    data = response.json()

    match = None
    for m in data.get("matches", []):
        if m["match_id"] == match_id:
            match = m
            break

    if not match:
        typer.echo(f"Match {match_id} not found for project {project_id}.")
        raise typer.Exit(code=1)

    typer.echo(f"\nMatch: {match['tier']} ({match['similarity']:.0%} similar)")
    typer.echo(f"Lifecycle: {match.get('other_project', {}).get('lifecycle_stage', 'unknown')}")

    other = match.get("other_project", {})
    lt = match.get("listing_type", "private")

    if lt != "private":
        typer.echo(f"Type: [{lt.upper()}]")
    if other.get("display_name"):
        typer.echo(f"Project: {other['display_name']}")
    if other.get("repo_url"):
        typer.echo(f"Repository: {other['repo_url']}")

    meta = other.get("repo_metadata")
    if meta:
        parts = []
        if meta.get("stars") is not None:
            parts.append(f"{meta['stars']} stars")
        if meta.get("license"):
            parts.append(meta["license"])
        if meta.get("contributor_count") is not None:
            parts.append(f"{meta['contributor_count']} contributors")
        if parts:
            typer.echo(f"  {' · '.join(parts)}")
        if meta.get("description"):
            typer.echo(f"  {meta['description']}")
        if meta.get("topics"):
            typer.echo(f"  Topics: {', '.join(meta['topics'])}")
        if meta.get("last_commit_at"):
            typer.echo(f"  Last commit: {meta['last_commit_at'][:10]}")
        if meta.get("scraped_at"):
            typer.echo(f"  Scraped: {meta['scraped_at'][:10]}")

    comparison = match.get("comparison")
    if not comparison:
        typer.echo("No comparison data available.")
        return

    typer.echo(f"\nArchitecture: {comparison['your_architecture']} vs {comparison['their_architecture']}"
               f" {'(match)' if comparison['architecture_match'] else '(different)'}")
    typer.echo(f"Lifecycle: {comparison['your_lifecycle_stage']} vs {comparison['their_lifecycle_stage']}")

    _print_comparison_section("Goals", comparison["shared_goals"], comparison["unique_to_yours"], comparison["unique_to_theirs"])
    _print_comparison_section("Languages", comparison["shared_languages"], comparison["unique_languages_yours"], comparison["unique_languages_theirs"])
    _print_comparison_section("Frameworks", comparison["shared_frameworks"], comparison["unique_frameworks_yours"], comparison["unique_frameworks_theirs"])
    _print_comparison_section("Libraries", comparison["shared_libraries"], comparison["unique_libraries_yours"], comparison["unique_libraries_theirs"])


def _print_comparison_section(title: str, shared: list[str], yours: list[str], theirs: list[str]):
    """Print a comparison section with shared/unique items."""
    if not shared and not yours and not theirs:
        return
    typer.echo(f"\n{title}:")
    if shared:
        typer.echo(f"  Shared: {', '.join(shared)}")
    if yours:
        typer.echo(f"  Only yours: {', '.join(yours)}")
    if theirs:
        typer.echo(f"  Only theirs: {', '.join(theirs)}")


@app.command()
def connect(match_id: str = typer.Argument(..., help="Match UUID to request introduction for"),
            project_id: str = typer.Argument(..., help="Your project UUID")):
    """Request an introduction for a match."""
    client = get_client()
    response = client.post(
        "/introductions",
        json={"match_id": match_id, "requester_project_id": project_id},
    )
    data = response.json()
    typer.echo(f"Introduction {data['status']}: {data['id']}")
    if data.get("target_contact_info"):
        typer.echo(f"Target contact info: {data['target_contact_info']}")
