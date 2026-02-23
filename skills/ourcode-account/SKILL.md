---
name: ourcode-account
description: Use when the developer wants to manage their OurCode account - view profile, set contact info, manage projects, view matches, request or respond to introductions
---

# OurCode Account Management

## Overview

Manage your OurCode account using the `ourcode` CLI. View your profile, set contact info, manage projects, browse matches, and handle introductions.

## Prerequisites

- Must be authenticated (run `/ourcode-login` first)
- The `ourcode` CLI must be installed (it's part of the server package)

## Available Commands

### Profile

```bash
# View your profile
ourcode profile show

# Set or update your contact info (required before requesting introductions)
ourcode profile set-contact "email: you@example.com, discord: yourname#1234"

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

# Show detailed comparison for a specific match
ourcode matches show <match-id> --project <project-id>

# Request an introduction for a match
ourcode matches connect <match-id> <your-project-id>
```

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

### First time setup

1. Run `ourcode profile show` to check your profile
2. Run `ourcode profile set-contact "<your contact info>"` — this is required before you can request or accept introductions

### Viewing and acting on matches

1. Run `ourcode projects list` to see your projects
2. Run `ourcode matches list <project-id>` to see matches for a project
3. Run `ourcode matches show <match-id> --project <project-id>` to see a detailed comparison of your project vs. a match
4. If interested in a match, run `ourcode matches connect <match-id> <your-project-id>`
   - If the target project has auto-approve: you'll see their contact info immediately
   - If manual: the request is pending until they accept

**Alternative:** Use the [web dashboard](https://our-code-production.up.railway.app) to browse matches, compare projects, and manage introductions with a graphical interface.

### Responding to introduction requests

1. Run `ourcode intros list` to see incoming requests
2. Run `ourcode intros accept <id>` to accept (reveals both parties' contact info)
3. Run `ourcode intros decline <id>` to decline

## Error Handling

- **"no API token found"**: Run `/ourcode-login` first
- **"must set contact_info"**: Run `ourcode profile set-contact "<info>"` first
- **"target project has introductions blocked"**: That project owner has disabled introductions
- **"active introduction already exists"**: You already have a pending or accepted introduction for this match
