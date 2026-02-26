# plugin/

<!-- Freshness: 2026-02-24 -->
<!-- Last contract review: 2026-02-24 -->

## Purpose

Claude Code plugin that provides five skills for interacting with the OurCode API: login via GitHub OAuth, generate a project summary from the current codebase, submit that summary to the server, manage your account (profile, matches, introductions), and a first-run setup flow that chains login, summarize, and submit.

## Structure

```
.claude-plugin/plugin.json   # Plugin manifest (name: "ourcode")
commands/                     # Slash command definitions (ourcode-login, ourcode-submit, ourcode-summarize, ourcode-setup)
skills/                       # Skill implementations
  ourcode-login/SKILL.md      # GitHub OAuth login (delegates to `ourcode auth login`)
  ourcode-summarize/SKILL.md  # Analyze codebase and produce ProjectSummaryCreate JSON
  ourcode-submit/SKILL.md     # Submit summary to POST /api/projects, display match comparison
  ourcode-account/SKILL.md    # Account management via ourcode CLI (matches show, /api/ paths)
  ourcode-setup/SKILL.md      # First-run setup: chains login -> summarize -> submit in one flow
src/cli/                      # Typer CLI (`ourcode` console script)
  auth.py                     # auth login/status/logout commands
  client.py                   # httpx API client, config read/write (~/.ourcode/config)
  main.py                     # CLI entrypoint, registers all subcommands
  profile.py, projects.py, matches.py, intros.py  # Account management subcommands
```

## Contracts

- **Login skill** delegates to `ourcode auth login`, which calls `POST /api/auth/sessions`, opens `auth_url` in browser, polls `GET /api/auth/sessions/{session_id}` until complete, stores the returned `api_token` via `save_config()`.
- **Summarize skill** analyzes the current project and produces a `ProjectSummaryCreate` JSON object matching schema_version "2.0".
- **Submit skill** sends the summary to `POST /api/projects` with Bearer token auth. Response includes `matches` array with similar projects grouped by tier (exact, partial, related), each containing decrypted summary, similarity score, and `comparison` data (shared/unique goals, tech stack, architecture).
- **Setup skill** chains login, summarize, and submit into a single first-run flow. Checks for existing token, runs subagent for codebase analysis, displays matches with comparison data, and offers next steps (dashboard, contact info, introductions).
- **Account skill** delegates to the `ourcode` CLI for profile management, match browsing (including `matches show` with comparison), and introduction handling. CLI reads config from `~/.ourcode/config`.
- **Profile set-contact** uses structured contact methods: `--method type:value` (repeatable), `--preferred type`, optional `--timezone` and `--notes`. Valid contact types: email, discord, linkedin, slack, twitter, github_discussion, other. The API payload is `{methods: [{type, value, preferred}], timezone?, notes?}` to `POST /api/developers/me/contact-info`.
- **Matches list** accepts an optional `--type` filter (private, public, scraped) passed as `?listing_type=` query param. Match output includes listing type, project display name, repo URL, and repo metadata (stars, license, contributors, topics, last commit, scraped date).
- **Contact info display** uses `format_contact_info()` in `client.py` which handles both structured (dict with methods array) and legacy plain-string formats.
- All API calls use the `/api/` prefix (e.g., `/api/auth/sessions`, `/api/projects`).
- The summary schema is defined in `server/app/schemas/summary.py` -- any changes there must be reflected in the summarize skill output.

## Publishing & Versioning

Releases are fully automated via [python-semantic-release](https://github.com/python-semantic-release/python-semantic-release) (v10). On every push to `main`, it analyzes commits and, if warranted, bumps the version in `pyproject.toml`, creates a git tag, builds with `uv build`, and creates a GitHub release. A separate publish job uploads to TestPyPI via `pypa/gh-action-pypi-publish`.

**Never manually edit the version in `pyproject.toml` or create version tags.** The tool manages both atomically.

Currently publishing to **TestPyPI**. To switch to prod PyPI: remove `repository-url` from the publish step in `release.yml` and change the secret from `TEST_PYPI_TOKEN` to `PYPI_TOKEN`.

**If `uv.lock` is added later**, update `build_command` in `pyproject.toml` to:
```toml
build_command = """
    uv lock --upgrade-package ourcode
    git add uv.lock
    uv build
"""
```
This ensures the lockfile is updated and included in the release commit.

### Conventional Commits

Commit messages control what gets released. A [commitizen](https://commitizen-tools.github.io/commitizen/) pre-commit hook (via `pre-commit`) enforces the format locally. Run `pre-commit install --hook-type commit-msg` after cloning.

| Commit prefix | Version bump | Example |
|---|---|---|
| `fix:` | Patch (0.0.x) | `fix: handle missing config file` |
| `feat:` | Minor (0.x.0) | `feat: add match filtering` |
| `feat!:` or `BREAKING CHANGE:` footer | Major (x.0.0) | `feat!: redesign CLI interface` |
| `chore:`, `docs:`, `refactor:`, `test:`, `ci:` | No release | `chore: update deps` |

**PR impact:** When squash-merging PRs, the squash commit message is what semantic-release reads. The PR title becomes the squash commit message by default in GitHub — so **PR titles must follow conventional commit format** to trigger the correct release.

Other valid scopes: `fix(auth):`, `feat(cli):`, etc. Scopes are optional but useful for changelogs.

## Dependencies

- Requires the OurCode server API to be running and reachable
- The `ourcode` CLI is part of this package (installed via `pip install ourcode` or `uv pip install ourcode`)
- Skills are markdown-based (SKILL.md) -- no compiled code
- Server-side contract tests (`server/tests/test_api_contract.py`) verify API response shapes match what the CLI expects
