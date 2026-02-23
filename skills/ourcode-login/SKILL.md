---
name: ourcode-login
description: Use when the developer needs to authenticate with OurCode via GitHub - runs `ourcode auth login` to create a session, open browser for GitHub OAuth, poll until complete, and save API token to ~/.ourcode/config
---

# OurCode Login

## Overview

Authenticate the developer with OurCode via GitHub. The `ourcode auth login` command handles the entire flow: creating a session on the server, opening the browser to GitHub OAuth, polling until authentication completes, and saving the API token locally.

## Prerequisites

- The `ourcode` CLI must be installed (`pip install ourcode` or `uv pip install ourcode`)
- Internet access to reach the OurCode API server
- A web browser for GitHub OAuth authorization

## Configuration

The API base URL defaults to `https://api.ourcode.dev`. Override by setting the `OURCODE_API_URL` environment variable.

## Steps

### Step 1: Run the login command

```bash
ourcode auth login
```

If the developer is already logged in, the command will report that and exit. To force re-authentication:

```bash
ourcode auth login --force
```

### Step 2: Report result

- If exit code 0: "Authentication successful! Your API token has been saved to `~/.ourcode/config`. You can now use `/ourcode-summarize` and `/ourcode-submit`."
- If exit code 1: Report the error message from the command output.

## Other auth commands

- **Check status**: `ourcode auth status` — verifies the saved token is valid
- **Log out**: `ourcode auth logout` — removes `~/.ourcode/config`

## Error Handling

- If the CLI is not installed: "The `ourcode` CLI is not installed. Install it with `pip install ourcode` or `uv pip install ourcode`."
- If the API server is unreachable: The CLI will print an error. Report it to the developer.
- If the session expires: The CLI will print an error. Suggest re-running `/ourcode-login`.

## Security Notes

- The API token is stored in plain text at `~/.ourcode/config`. This is acceptable for a CLI tool (similar to `~/.npmrc` or `~/.docker/config.json`).
- Tokens are long-lived (90 days). Re-run `/ourcode-login` to get a fresh token if expired.
