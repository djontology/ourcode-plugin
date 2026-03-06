# OurCode

Find developers working on similar projects. Authenticate with GitHub, generate a structured summary of your codebase, and get matched with others building related things.

This repo contains:
- **Claude Code plugin** — analyze and submit projects from within Claude Code
- **CLI** — manage your profile, matches, and introductions from the terminal

## Plugin Install

Install the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin:

```
/plugin marketplace add djontology/ourcode-plugin
/plugin install ourcode@ourcode-marketplace
```

Then run the setup flow from any project:

```
/ourcode-setup
```

This walks you through:
1. **Login** — authenticate via GitHub OAuth
2. **Summarize** — analyze your codebase and generate a project summary
3. **Submit** — send the summary and see your matches

### Plugin Commands

| Command | Description |
|---------|-------------|
| `/ourcode-setup` | First-run flow (login + summarize + submit) |
| `/ourcode-summarize` | Generate a project summary |
| `/ourcode-submit` | Submit your summary and view matches |
| `/ourcode-account` | Manage profile, matches, and introductions |

## CLI Install

```bash
pipx install ourcode
```

Or with uv:

```bash
uv tool install ourcode
```

The CLI reads its config from `~/.ourcode/config` (created automatically when you log in via the plugin).

### CLI Commands

```
ourcode profile show              # View your profile
ourcode profile set-contact       # Set contact info for introductions
ourcode profile delete-account    # Delete your account

ourcode projects list             # List your projects
ourcode projects show <id>        # Show project details
ourcode projects delete <id>      # Delete a project

ourcode matches list              # List your matches
ourcode matches show <id>         # Show match details with comparison

ourcode intros list               # List introductions
ourcode intros request <match>    # Request an introduction
ourcode intros accept <id>        # Accept an introduction
ourcode intros decline <id>       # Decline an introduction
```

## Dashboard

View your matches and manage introductions at [our-code-production.up.railway.app](https://our-code-production.up.railway.app).

## License

MIT
