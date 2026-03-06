---
name: ourcode-account
description: Use when the developer wants to manage their OurCode account - view profile, set contact info, manage projects, view matches, request or respond to introductions
---

# OurCode Account Management

## Overview

Manage your OurCode account using the `ourcode` CLI. View your profile, set contact info, manage projects, browse matches, and handle introductions.

## Prerequisites

- Must be authenticated (run `ourcode auth login` first)
- The `ourcode` CLI must be installed. Install with:
  ```bash
  pipx install ourcode
  # or
  uv tool install ourcode
  ```

## Available Commands

### Profile

```bash
# View your profile
ourcode profile show

# Set structured contact info
ourcode profile set-contact -m email:you@example.com -p email

# Multiple contact methods
ourcode profile set-contact -m email:you@example.com -m discord:yourname#1234 -p email

# With timezone and notes
ourcode profile set-contact -m email:you@example.com -p email -t America/New_York -n "Available evenings"

# Delete your account and all data (irreversible)
ourcode profile delete
```

### Projects

```bash
# List your projects
ourcode projects list

# Delete a project
ourcode projects delete <project-id>
```

### Matches

```bash
# List matches for a project
ourcode matches list <project-id>

# Filter matches by listing type
ourcode matches list <project-id> --type scraped

# Show detailed comparison for a specific match
ourcode matches show <match-id> --project <project-id>

# Request an introduction for a match
ourcode matches connect <match-id> <your-project-id>
```

**Match types:**
- **Private/Public matches**: Human-submitted projects. Request an introduction to connect with the developer.
- **Scraped matches**: Open-source repositories. Visit the repo URL directly — no introduction needed.

### Introductions

```bash
# List incoming and outgoing introductions
ourcode intros list

# Accept an incoming introduction (reveals both parties' contact info)
ourcode intros accept <introduction-id>

# Decline an incoming introduction
ourcode intros decline <introduction-id>
```

## Workflow Guide

### First time after submitting a project

1. Run `ourcode profile show` to check your profile
2. Run `ourcode profile set-contact -m email:you@example.com -p email` — required before you can request or accept introductions

### Viewing and acting on matches

1. Run `ourcode projects list` to see your projects
2. Run `ourcode matches list <project-id>` to see matches for a project
3. Run `ourcode matches show <match-id> --project <project-id>` to see a detailed comparison
4. If interested, run `ourcode matches connect <match-id> <your-project-id>`
   - If the target project has auto-approve: you'll see their contact info immediately
   - If manual: the request is pending until they accept

### Responding to introduction requests

1. Run `ourcode intros list` to see incoming requests
2. Run `ourcode intros accept <id>` to accept (reveals both parties' contact info)
3. Run `ourcode intros decline <id>` to decline

**Web alternative:** You can also do all of this from the [dashboard](https://our-code-production.up.railway.app) — browse matches, compare projects, and manage introductions with a visual interface.

## Error Handling

- **"no API token found"**: Run `ourcode auth login` first
- **"must set contact_info"**: Run `ourcode profile set-contact` with contact methods first
- **"target project has introductions blocked"**: That project owner has disabled introductions. If it's a scraped open-source repo, visit the repo URL directly instead.
- **"active introduction already exists"**: You already have a pending or accepted introduction for this match
