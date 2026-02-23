"""OurCode CLI — authentication, account management, matches, and introductions."""

import typer

from cli import auth, intros, matches, profile, projects

app = typer.Typer(help="OurCode CLI for account management")
app.add_typer(auth.app, name="auth")
app.add_typer(profile.app, name="profile")
app.add_typer(projects.app, name="projects")
app.add_typer(matches.app, name="matches")
app.add_typer(intros.app, name="intros")


def main():
    """Entry point for console script."""
    import httpx

    try:
        app()
    except httpx.HTTPStatusError as e:
        typer.echo(f"API error {e.response.status_code}: {e.response.text}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()
