"""OurCode CLI — authentication, account management, matches, and introductions."""

import os

import typer

from cli import auth, intros, matches, profile, projects

app = typer.Typer(help="OurCode CLI for account management")
app.add_typer(auth.app, name="auth")
app.add_typer(profile.app, name="profile")
app.add_typer(projects.app, name="projects")
app.add_typer(matches.app, name="matches")
app.add_typer(intros.app, name="intros")


@app.callback()
def _callback(
    no_update_check: bool = typer.Option(
        False, "--no-update-check", help="Skip checking for CLI updates"
    ),
) -> None:
    if no_update_check:
        os.environ["OURCODE_NO_UPDATE_CHECK"] = "1"

    from cli.update_check import start_background_check

    start_background_check()


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
