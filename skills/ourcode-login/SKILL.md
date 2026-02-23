---
name: ourcode-login
description: Use when the developer needs to authenticate with OurCode via GitHub - creates a session, opens browser for GitHub OAuth, polls until complete, and saves API token to ~/.ourcode/config
---

# OurCode Login

## Overview

Authenticate the developer with OurCode via GitHub. Uses a session polling pattern: create a session on the server, open the browser to GitHub OAuth, poll until authentication completes, then save the API token locally.

## Prerequisites

- Internet access to reach the OurCode API server
- A web browser for GitHub OAuth authorization

## Configuration

The API base URL defaults to `https://api.ourcode.dev`. Override by setting the `OURCODE_API_URL` environment variable.

## Steps

### Step 1: Check for existing token

Read `~/.ourcode/config` to check if a token already exists.

```bash
cat ~/.ourcode/config 2>/dev/null
```

If a valid token exists, inform the developer:
"You are already logged in. Run `/ourcode-login` again to re-authenticate with a fresh token."

If the developer explicitly wants to re-authenticate, continue to Step 2.

### Step 2: Determine API base URL

```bash
echo "${OURCODE_API_URL:-https://api.ourcode.dev}"
```

Use this as `API_BASE` for all subsequent requests.

### Step 3: Create an auth session

```bash
curl -s -X POST "${API_BASE}/api/auth/sessions" -H "Content-Type: application/json"
```

Expected response:
```json
{"session_id": "uuid-here", "auth_url": "https://github.com/login/oauth/authorize?client_id=...&state=uuid-here"}
```

Extract `session_id` and `auth_url` from the response.

### Step 4: Open browser for GitHub authorization

```bash
open "${auth_url}"
```

Tell the developer: "Opening your browser to sign in with GitHub. Please authorize the OurCode app."

### Step 5: Poll for session completion

Poll the session status every 2 seconds for up to 5 minutes (150 attempts):

```bash
curl -s "${API_BASE}/api/auth/sessions/${session_id}"
```

- If `status` is `"pending"`: wait 2 seconds and retry
- If `status` is `"complete"`: extract `api_token` and proceed to Step 6
- If `status` is `"expired"`: inform the developer the session timed out and suggest re-running `/ourcode-login`

### Step 6: Save the API token

Create the config directory and write the token:

```bash
mkdir -p ~/.ourcode
```

Write to `~/.ourcode/config`:

```
OURCODE_API_TOKEN=<the api_token from step 5>
OURCODE_API_URL=<the API_BASE used>
```

### Step 7: Confirm success

Tell the developer: "Authentication successful! Your API token has been saved to `~/.ourcode/config`. You can now use `/ourcode-summarize` and `/ourcode-submit`."

## Error Handling

- If the API server is unreachable: "Cannot reach the OurCode server. Check your internet connection and try again."
- If GitHub authorization is denied: The session will remain pending until it expires. Inform the developer.
- If the session expires (10 minutes): "Session timed out. Please run `/ourcode-login` again."

## Security Notes

- The API token is stored in plain text at `~/.ourcode/config`. This is acceptable for a CLI tool (similar to `~/.npmrc` or `~/.docker/config.json`).
- Tokens are long-lived (90 days). Re-run `/ourcode-login` to get a fresh token if expired.
