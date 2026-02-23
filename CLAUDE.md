# plugin/

<!-- Freshness: 2026-02-22 -->

## Purpose

Claude Code plugin that provides five skills for interacting with the OurCode API: login via GitHub OAuth, generate a project summary from the current codebase, submit that summary to the server, manage your account (profile, matches, introductions), and a first-run setup flow that chains login, summarize, and submit.

## Structure

```
.claude-plugin/plugin.json   # Plugin manifest (name: "ourcode", v0.1.0)
commands/                     # Slash command definitions (ourcode-login, ourcode-submit, ourcode-summarize, ourcode-setup)
skills/                       # Skill implementations
  ourcode-login/SKILL.md      # GitHub OAuth login
  ourcode-summarize/SKILL.md  # Analyze codebase and produce ProjectSummaryCreate JSON
  ourcode-submit/SKILL.md     # Submit summary to POST /api/projects, display match comparison
  ourcode-account/SKILL.md    # Account management via ourcode CLI (matches show, /api/ paths)
  ourcode-setup/SKILL.md      # First-run setup: chains login -> summarize -> submit in one flow
```

## Contracts

- **Login skill** calls `POST /api/auth/sessions`, opens `auth_url` in browser, polls `GET /api/auth/sessions/{session_id}` until complete, stores the returned `api_token`.
- **Summarize skill** analyzes the current project and produces a `ProjectSummaryCreate` JSON object matching schema_version "1.0".
- **Submit skill** sends the summary to `POST /api/projects` with Bearer token auth. Response includes `matches` array with similar projects grouped by tier (exact, partial, related), each containing decrypted summary, similarity score, and `comparison` data (shared/unique goals, tech stack, architecture).
- **Setup skill** chains login, summarize, and submit into a single first-run flow. Checks for existing token, runs subagent for codebase analysis, displays matches with comparison data, and offers next steps (dashboard, contact info, introductions).
- **Account skill** delegates to the `ourcode` CLI for profile management, match browsing (including `matches show` with comparison), and introduction handling. CLI reads config from `~/.ourcode/config`.
- All API calls use the `/api/` prefix (e.g., `/api/auth/sessions`, `/api/projects`).
- The summary schema is defined in `server/app/schemas/summary.py` -- any changes there must be reflected in the summarize skill output.

## Dependencies

- Requires the OurCode server API to be running and reachable
- Account skill requires the `ourcode` CLI to be installed (`uv sync` in server/)
- Skills are markdown-based (SKILL.md) -- no compiled code
