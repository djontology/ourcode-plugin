---
name: ourcode-submit
description: Use when the developer wants to submit their project summary to OurCode for matching - reads saved token and summary, submits to the API, shows matches (which are persisted for later access), and offers to register or keep as ephemeral
---

# OurCode Submit

## Overview

Submit the project summary to the OurCode server for matching. Reads the API token from `~/.ourcode/config` and the summary from `.ourcode/summary.json`, sends it to the server, and shows the result. The developer chooses whether to register the project permanently or keep it as an ephemeral 24-hour search.

## Prerequisites

- Must be authenticated (run `/ourcode-login` first)
- Must have a summary generated (run `/ourcode-summarize` first)

## Steps

### Step 1: Verify authentication

```bash
ourcode auth status
```

If exit code 1: "You need to authenticate first. Run `/ourcode-login`."

### Step 2: Read the project summary

Read `.ourcode/summary.json` from the project root.

If the file doesn't exist: "No project summary found. Run `/ourcode-summarize` first."

Parse the JSON and verify it has the required fields (`schema_version`, `project`, `tech_stack`).

### Step 3: Ask about registration

Ask the developer:

"Would you like to register this project permanently, or submit it as an ephemeral search (auto-deleted after 24 hours)?"

Options:
- **Register permanently** — project stays on your account, matches are saved
- **Ephemeral search** — submit for matching, auto-expires in 24 hours. You can register it later if you find good matches.

### Step 4: Submit to the server

Read token and API URL from `~/.ourcode/config`. Default API URL: `https://our-code-production.up.railway.app`

There is no CLI command for project submission yet, so submit directly via the API:

```bash
curl -s -X POST "${OURCODE_API_URL}/api/projects?register=true" \
  -H "Authorization: Bearer ${OURCODE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @.ourcode/summary.json
```

(Use `register=false` for ephemeral.)

### Step 5: Show the result

Parse the response and display:

- **Project ID**: the assigned UUID
- **Status**: registered or ephemeral
- **Expires**: expiry time if ephemeral, "never" if registered

Then check the `matches` array in the response.

**If matches exist**, display them grouped by tier:

"Project submitted successfully!
- Project ID: `abc123-def456-...`
- Status: Registered

Found **3 similar projects**:

**Exact matches** (very similar goals and tech):
  - 94% similar (mvp)
    Goals: Build a developer matching service
    Tech: Python, FastAPI, pgvector

**Partial matches** (overlapping goals, different approach):
  - 82% similar (prototype)
    Goals: Create a developer discovery platform
    Tech: TypeScript, Next.js, Pinecone

**Related projects** (same domain, adjacent goals):
  - 68% similar (ga)
    Goals: Open source contributor matching
    Tech: Go, PostgreSQL"

For each matched project, extract from `matches[].summary`:
- Goals: `summary.project.goals` (join with "; ")
- Tech: `summary.tech_stack.languages` + `summary.tech_stack.frameworks` (join with ", ")

### Displaying Match Comparison Data

For each match that includes a `comparison` field in the response, display the structured comparison:

```
**Shared goals:** [list shared_goals]
**Your unique goals:** [list unique_to_yours]
**Their unique goals:** [list unique_to_theirs]
**Shared tech:** [list shared_languages, shared_frameworks, shared_libraries]
**Architecture:** [your_architecture] vs [their_architecture] (match: yes/no)
**Lifecycle:** [your_lifecycle_stage] vs [their_lifecycle_stage]
```

**If no matches**, display:

"Project submitted successfully!
- Project ID: `abc123-def456-...`
- Status: Registered

No similar projects found yet. As more developers submit projects, matches will appear."

### Step 6: Handle errors

- **401 Unauthorized**: "Your API token is invalid or expired. Run `ourcode auth login --force` to re-authenticate."
- **422 Validation Error**: "Your summary doesn't match the expected schema. Run `/ourcode-summarize` to regenerate it."
- **500 Server Error**: "The OurCode server encountered an error. Please try again later."
- **Network error**: "Cannot reach the OurCode server. Check your internet connection."

### Step 7: Offer next steps

After displaying results, mention:

"Your matches have been saved. You can revisit them anytime:
- **Web dashboard**: https://our-code-production.up.railway.app
- **CLI**: `ourcode matches list <project-id>`

Want to connect with a match? First set your contact info:
```bash
ourcode profile set-contact 'email: you@example.com'
```

Then request an introduction:
```bash
ourcode matches connect <match-id> <your-project-id>
```

Run `/ourcode-account` for full account management."
