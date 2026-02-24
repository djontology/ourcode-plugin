---
name: ourcode-setup
description: First-run setup for OurCode — authenticate, analyze your codebase, and submit your project in one flow
user-invocable: true
---

# OurCode Setup

One command to set up OurCode: authenticate with GitHub, analyze your codebase, and submit your project to find matches.

## Step 1: Verify CLI is installed

Check whether the `ourcode` CLI is available:

```bash
which ourcode
```

**If found:** Skip to Step 2.

**If not found:** The CLI needs to be installed. Check for a package installer:

```bash
which uv || which uvx || which pipx
```

- **If `uv` or `uvx` is available:**
  ```bash
  uv tool install git+https://github.com/djontology/ourcode-plugin.git
  ```

- **If `pipx` is available:**
  ```bash
  pipx install git+https://github.com/djontology/ourcode-plugin.git
  ```

- **If none are available:** Walk the user through installing `uv` first:

  "You'll need a Python package installer. The fastest option is `uv`:"

  On macOS/Linux:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

  On Windows:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

  After installing `uv`, restart the shell (or `source ~/.bashrc` / `source ~/.zshrc`), then install the CLI:
  ```bash
  uv tool install git+https://github.com/djontology/ourcode-plugin.git
  ```

Verify the install succeeded:
```bash
ourcode --help
```

## Step 2: Authenticate

Check for an existing token:

```bash
ourcode auth status
```

- **If exit code 0:** Already authenticated. Skip to Step 3.
- **If exit code 1 or token missing:** Run the login command:

```bash
ourcode auth login
```

This opens a browser for GitHub OAuth, polls until complete, and saves the token to `~/.ourcode/config`.

If login fails, report the error and offer to retry.

## Step 3: Analyze Codebase

Use a subagent to analyze the current project and produce a `ProjectSummaryCreate` JSON payload.

### Subagent Instructions

Dispatch a subagent with these instructions:

> Analyze this codebase and produce a JSON object matching the ProjectSummaryCreate schema:
>
> ```json
> {
>   "schema_version": "1.0",
>   "project": {
>     "goals": ["list of 2-5 project goals"],
>     "domain_tags": ["relevant domain tags"],
>     "architecture": "one of: monolith, microservices, cli-tool, library, web-app, mobile-app, api-service",
>     "lifecycle_stage": "one of: brainstorm, prototype, mvp, ga"
>   },
>   "tech_stack": {
>     "languages": ["programming languages used"],
>     "frameworks": ["frameworks used"],
>     "key_libraries": ["important libraries"],
>     "infrastructure": ["infrastructure tools"]
>   }
> }
> ```
>
> Read these files to determine the summary:
> - README.md (or README) for project goals and description
> - package.json, pyproject.toml, Cargo.toml, go.mod, or other package manifests for tech stack
> - Dockerfile, docker-compose.yml for infrastructure
> - Directory structure for architecture style
>
> Return ONLY the JSON object, no explanation.

### Fallback: Manual Input

If the subagent cannot determine enough information (no README, no package manifests):

1. Ask the user for project goals (what does this project do?)
2. Ask for tech stack (languages, frameworks, libraries)
3. Ask for domain tags
4. Ask for lifecycle stage (brainstorm, prototype, mvp, ga)
5. Ask for architecture style

Construct the ProjectSummaryCreate JSON from the answers.

## Step 4: Review and Edit

Show the generated summary to the user in a readable format:

```
Project Summary:
  Goals: [list]
  Domain: [tags]
  Architecture: [style]
  Stage: [lifecycle_stage]

Tech Stack:
  Languages: [list]
  Frameworks: [list]
  Libraries: [list]
  Infrastructure: [list]
```

Ask: "Does this look correct? You can edit any field before submission."

If the user wants changes, update the JSON accordingly.

## Step 5: Submit Project

Read token and API URL from `~/.ourcode/config`. Default API URL: `https://our-code-production.up.railway.app`

There is no CLI command for project submission yet, so submit directly via the API:

```bash
curl -s -X POST "${API_BASE}/api/projects?register=true" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '${SUMMARY_JSON}'
```

If the response includes an error, show it and offer to fix the summary.

## Step 6: Display Matches

Parse the response. Matches are in the `matches` array, grouped by tier:
- **exact** (>88% similar)
- **partial** (75-88% similar)
- **related** (65-75% similar)

For each match, display:
- Tier badge and similarity percentage
- Lifecycle stage
- Goals preview

If the match includes a `comparison` field, show:
- **Shared goals:** [shared_goals]
- **Your unique goals:** [unique_to_yours]
- **Their unique goals:** [unique_to_theirs]
- **Shared tech:** [shared_languages, shared_frameworks]
- **Architecture:** [comparison] (match/different)

## Step 7: Next Steps

After displaying matches, offer:

1. **Web dashboard:** "Visit https://our-code-production.up.railway.app to browse matches, compare projects, and manage introductions"
2. **Set contact info:** `ourcode profile set-contact <your-email>`
3. **Request introduction:** `ourcode matches connect <match-id> <project-id>`
4. **View matches later:** `ourcode matches list <project-id>`
5. **Account management:** "Run `/ourcode-account` for full account management"

## Error Handling

- **Network errors:** If any API call fails, show the error and suggest checking connectivity.
- **401 Unauthorized:** Token may be expired. Run `ourcode auth login --force` to re-authenticate.
- **422 Validation Error:** Summary doesn't match schema. Show the error details and let user fix.
