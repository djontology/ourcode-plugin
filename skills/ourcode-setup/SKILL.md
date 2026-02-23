---
name: ourcode-setup
description: First-run setup for OurCode — authenticate, analyze your codebase, and submit your project in one flow
user-invocable: true
---

# OurCode Setup

One command to set up OurCode: authenticate with GitHub, analyze your codebase, and submit your project to find matches.

## Step 1: Check Authentication

Read `~/.ourcode/config` and check for `OURCODE_API_TOKEN`.

- **If token exists:** Skip to Step 2. Say "Already authenticated."
- **If no token:** Run the login flow:

### Login Flow

1. Read the API base URL from `~/.ourcode/config` `OURCODE_API_URL` field. Default: `https://our-code-production.up.railway.app`
2. Create a session:
   ```bash
   curl -s -X POST "${API_BASE}/api/auth/sessions" -H "Content-Type: application/json" | jq .
   ```
   Extract `session_id` and `auth_url` from the response.
3. Tell the user: "Open this URL to authenticate with GitHub: [auth_url]"
4. Poll for completion:
   ```bash
   curl -s "${API_BASE}/api/auth/sessions/${SESSION_ID}" | jq .
   ```
   Poll every 2 seconds, up to 150 attempts. When `status` is `complete`, extract `api_token`.
5. Save token to `~/.ourcode/config`:
   ```
   OURCODE_API_TOKEN=<api_token>
   OURCODE_API_URL=<api_base>
   ```
6. If session expires or polling times out, tell the user and offer to retry.

## Step 2: Analyze Codebase

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

## Step 3: Review and Edit

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

## Step 4: Submit Project

Read token from `~/.ourcode/config` `OURCODE_API_TOKEN`.
Read API URL from `~/.ourcode/config` `OURCODE_API_URL`. Default: `https://our-code-production.up.railway.app`

Submit the project:
```bash
curl -s -X POST "${API_BASE}/api/projects?register=true" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '${SUMMARY_JSON}' | jq .
```

If the response includes an error, show it and offer to fix the summary.

## Step 5: Display Matches

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

## Step 6: Next Steps

After displaying matches, offer:

1. **View dashboard:** "Visit https://our-code-production.up.railway.app to see your matches in a web dashboard"
2. **Set contact info:** "Run `ourcode profile set-contact <your-email>` to enable introductions"
3. **Request introduction:** "Run `ourcode matches connect <match-id> <project-id>` to connect with a match"
4. **Account management:** "Run `/ourcode-account` for full account management"

## Error Handling

- **Network errors:** If any API call fails, show the error and suggest checking connectivity.
- **401 Unauthorized:** Token may be expired. Clear `~/.ourcode/config` and restart from Step 1.
- **422 Validation Error:** Summary doesn't match schema. Show the error details and let user fix.
