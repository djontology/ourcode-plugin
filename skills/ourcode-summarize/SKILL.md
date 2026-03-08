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
  "schema_version": "2.0",
  "display_name": "string — short project name, 1-100 chars",
  "project": {
    "goals": ["string — freeform goal description"],
    "non_goals": ["string — what this project explicitly does NOT do"],
    "user_stories": ["As a [persona], I [action/need]"],
    "domain_tags": ["string — categorization keyword"],
    "ux_patterns": ["string — e.g. crud-dashboard, cli-tool, visual-canvas"],
    "architecture": "monolith | microservices | cli-tool | library | web-app | mobile-app | api-service",
    "lifecycle_stage": "building | dogfood | community | product"
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

### Step 1: Analyze and draft the summary

Dispatch the `ourcode:codebase-summarizer` agent via the Task tool to analyze the codebase and produce a `ProjectSummaryCreate` JSON summary. The agent reads README, package manifests, directory structure, and infrastructure files, then returns the JSON object.

If the agent cannot determine enough information (no README, no package manifests), ask the developer to describe their project goals, tech stack, domain tags, lifecycle stage, and architecture style. Construct the JSON from their answers.

### Step 2: Present to developer for review

Output the drafted summary as formatted JSON and ask the developer to review it:

"Here's the project summary I've drafted. Please review and let me know if you'd like to adjust anything:"

Display the summary in a readable format:

```
Project Summary:
  Name: [display_name]
  Goals: [list]
  User Stories: [list]
  Non-Goals: [list, or "None"]
  Domain: [tags]
  UX Patterns: [list]
  Architecture: [style]
  Stage: [lifecycle_stage]

Tech Stack:
  Languages: [list]
  Frameworks: [list]
  Libraries: [list]
  Infrastructure: [list]
```

Also show the full JSON for reference.

Ask: "Does this look accurate? Would you like to change anything before saving?"

### Step 3: Save the summary

Once the developer approves, write the summary to `.ourcode/summary.json` in the project root:

```bash
mkdir -p .ourcode
```

Write the approved JSON to `.ourcode/summary.json`.

Tell the developer: "Summary saved to `.ourcode/summary.json`. Run `/ourcode-submit` to submit it for matching."

## Important Notes

- This skill works entirely offline. No network requests are made.
- No source code content is included in the summary.
- The developer always reviews and approves the summary before it's saved.
- If the project has insufficient information to generate a summary, ask the developer to describe their project goals directly.
