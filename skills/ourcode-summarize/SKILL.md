---
name: ourcode-summarize
description: Use when the developer wants to generate a project summary for OurCode - analyzes the local codebase to produce a structured JSON summary of goals, tech stack, architecture, and lifecycle stage without transmitting source code
---

# OurCode Summarize

## Overview

Analyze the current project and generate a structured JSON summary. The summary captures goals, tech stack, architecture pattern, and lifecycle stage. No source code or implementation details are included — only high-level metadata suitable for matching with similar projects.

## Output Format

The summary must conform to this schema:

```json
{
  "schema_version": "1.0",
  "project": {
    "goals": ["string — freeform goal description"],
    "domain_tags": ["string — categorization keyword"],
    "architecture": "monolith | microservices | cli-tool | library | web-app | mobile-app | api-service",
    "lifecycle_stage": "brainstorm | prototype | mvp | ga"
  },
  "tech_stack": {
    "languages": ["string"],
    "frameworks": ["string"],
    "key_libraries": ["string"],
    "infrastructure": ["string"]
  }
}
```

## Steps

### Step 1: Analyze the project

Read these files (if they exist) to understand the project:

1. **README.md** or similar documentation — extract project goals and description
2. **Package manifests** — detect languages, frameworks, and libraries:
   - `package.json` (Node.js/JavaScript/TypeScript)
   - `pyproject.toml` or `requirements.txt` (Python)
   - `Cargo.toml` (Rust)
   - `go.mod` (Go)
   - `Gemfile` (Ruby)
   - `pom.xml` or `build.gradle` (Java)
   - `*.csproj` (C#/.NET)
3. **Directory structure** — infer architecture pattern:
   - `src/` with subdirectories → likely monolith or web-app
   - `packages/` or `services/` → likely microservices
   - `lib/` → likely library
   - `cmd/` → likely cli-tool
   - `ios/` or `android/` → likely mobile-app
4. **Infrastructure files** — detect infrastructure:
   - `Dockerfile`, `docker-compose.yml` → Docker
   - `railway.toml`, `railway.json` → Railway
   - `vercel.json` → Vercel
   - `terraform/`, `*.tf` → Terraform
   - `.github/workflows/` → GitHub Actions
   - `Procfile` → Heroku

### Step 2: Draft the summary

Based on the analysis, draft a JSON summary. Use your best judgment for:

- **goals**: 1-3 concise descriptions of what the project aims to achieve
- **domain_tags**: 2-5 keywords for categorization (e.g., "e-commerce", "developer-tools", "data-pipeline")
- **architecture**: Choose the closest match from the allowed values
- **lifecycle_stage**: Assess based on README, test coverage, CI/CD presence:
  - `brainstorm` — mostly docs, no working code
  - `prototype` — working code, minimal tests, no CI
  - `mvp` — tests exist, CI exists, core features work
  - `ga` — production-ready, comprehensive tests, monitoring

### Step 3: Present to developer for review

Output the drafted summary as formatted JSON and ask the developer to review it:

"Here's the project summary I've drafted. Please review and let me know if you'd like to adjust anything:"

```json
{ ... drafted summary ... }
```

Ask: "Does this look accurate? Would you like to change anything before saving?"

### Step 4: Save the summary

Once the developer approves, write the summary to `.ourcode/summary.json` in the project root:

```bash
mkdir -p .ourcode
```

Write the approved JSON to `.ourcode/summary.json`.

Tell the developer: "Summary saved to `.ourcode/summary.json`. Run `/ourcode-submit` to submit it to OurCode for matching."

## Important Notes

- This Skill works entirely offline. No network requests are made.
- No source code content is included in the summary.
- The developer always reviews and approves the summary before it's saved.
- If the project has insufficient information to generate a summary, ask the developer to describe their project goals directly.
