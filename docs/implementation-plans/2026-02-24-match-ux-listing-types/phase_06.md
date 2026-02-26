# Match UX: Plugin & CLI Updates Implementation Plan

**Goal:** Update the CLI and plugin skills to render listing types, structured contact info, and repo metadata from the updated server API

**Architecture:** The `ourcode` CLI (Typer-based Python) renders API responses as formatted terminal output. Each CLI module (`matches.py`, `profile.py`, `intros.py`, `projects.py`) reads JSON from the server's `APIClient` and displays with `typer.echo`. Skills (`SKILL.md` files) document how the Claude Code plugin should interact with these commands. Changes are pure presentation — no new API endpoints, no new dependencies.

**Tech Stack:** Python 3.11+, Typer, httpx, pytest with `typer.testing.CliRunner`

**Scope:** 1 phase (Phase 6 of 6 from original design)

**Codebase verified:** 2026-02-24

---

## Acceptance Criteria Coverage

This phase implements and tests:

### match-ux-listing-types.AC3: Unified match feed
- **match-ux-listing-types.AC3.1 Success:** Match results include `listing_type`, `display_name`, `repo_url`, `repo_metadata` fields
- **match-ux-listing-types.AC3.2 Success:** Scraped repo matches show full repo metadata (stars, license, last commit, contributors, scraped_at)
- **match-ux-listing-types.AC3.3 Success:** Private project matches have null `repo_url` and `repo_metadata`
- **match-ux-listing-types.AC3.5 Success:** Optional `?listing_type=scraped` filter returns only scraped matches

### match-ux-listing-types.AC2: Structured contact info
- **match-ux-listing-types.AC2.1 Success:** Contact info with one method marked preferred validates and stores correctly
- **match-ux-listing-types.AC2.2 Success:** Contact info with multiple methods (one preferred) validates
- **match-ux-listing-types.AC2.3 Success:** All known contact types accepted (`email`, `discord`, `linkedin`, `slack`, `twitter`, `github_discussion`, `other`)

### match-ux-listing-types.AC5: Introduction flow with listing types
- **match-ux-listing-types.AC5.2 Success:** Introduction to public project auto-approves (status = accepted, contact info returned immediately)
- **match-ux-listing-types.AC5.3 Success:** Accepted introduction returns structured contact info (methods array, timezone, notes) for both parties

### match-ux-listing-types.AC6: Profile completeness
- **match-ux-listing-types.AC6.1 Success:** `GET /developers/me` returns `contact_method_count` reflecting number of stored methods

---

## Reference Files

These files document testing conventions and project structure — task-implementor should read them before writing code:

- `/Users/john/codez/our-code/ourcode-plugin/CLAUDE.md` — project contracts and structure
- `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py` — existing test patterns (CliRunner, _mock_client, _set_response, autouse fixtures)

---

<!-- START_SUBCOMPONENT_A (tasks 1-2) -->
**Note:** Tasks 1 and 2 both modify `matches.py`. Execute them in order — Task 1 first, then Task 2. Task 2's line numbers assume Task 1's changes are already applied.

<!-- START_TASK_1 -->
### Task 1: Update match list display with listing type and display name

**Verifies:** match-ux-listing-types.AC3.1, match-ux-listing-types.AC3.3, match-ux-listing-types.AC3.5

**Files:**
- Modify: `/Users/john/codez/our-code/ourcode-plugin/src/cli/matches.py:10-27` (list_matches command)

**Implementation:**

Update the `list_matches` command to:
1. Add a `Type` column to the table header and rows, reading from `m.get("listing_type", "private")`
2. Keep the existing `Status` column (introduction_status) — do not remove it
3. Add a `Name` column showing `display_name` from `other_project` when available
4. Add an optional `--type` filter parameter that appends `?listing_type=<value>` to the API request URL

Replace the `list_matches` function (lines 10-27) with:

```python
@app.command("list")
def list_matches(
    project_id: str = typer.Argument(..., help="Project UUID"),
    listing_type: str = typer.Option(None, "--type", help="Filter by listing type (private, public, scraped)"),
):
    """List matches for a project."""
    client = get_client()
    url = f"/projects/{project_id}/matches"
    if listing_type:
        url += f"?listing_type={listing_type}"
    response = client.get(url)
    data = response.json()
    matches = data.get("matches", [])
    if not matches:
        typer.echo("No matches found.")
        return
    typer.echo(f"{'Match ID':<38} {'Type':<10} {'Tier':<10} {'Similarity':<12} {'Status':<12} {'Name'}")
    typer.echo("-" * 100)
    for m in matches:
        lt = m.get("listing_type", "private")
        status = m.get("introduction_status") or "-"
        name = m.get("other_project", {}).get("display_name") or "-"
        typer.echo(
            f"{m['match_id']:<38} {lt:<10} {m['tier']:<10} "
            f"{m['similarity']:<12.4f} {status:<12} {name}"
        )
```

**Testing:**
Tests must verify each AC listed above:
- match-ux-listing-types.AC3.1: Match list output includes listing_type column and display_name
- match-ux-listing-types.AC3.3: Private project matches show "-" for name when display_name is null
- match-ux-listing-types.AC3.5: `--type scraped` appends `?listing_type=scraped` to the API call

Follow the existing pattern in `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`:
- Use `CliRunner` with `runner.invoke(matches_app, ["list", "proj-1"])`
- Mock API responses via `_set_response(client, {...})` with `listing_type` and `other_project.display_name` fields
- For the filter test, assert `client.get` was called with the query parameter in the URL

**Verification:**
Run: `cd /Users/john/codez/our-code/ourcode-plugin && uv run python -m pytest tests/ -v -k "match"`
Expected: All match tests pass

**Commit:** `feat(cli): add listing type and display name to match list output`
<!-- END_TASK_1 -->

<!-- START_TASK_2 -->
### Task 2: Update match show display with repo metadata for scraped projects

**Verifies:** match-ux-listing-types.AC3.1, match-ux-listing-types.AC3.2

**Files:**
- Modify: `/Users/john/codez/our-code/ourcode-plugin/src/cli/matches.py:30-78` (show command and _print_comparison_section)

**Implementation:**

Update the `show` command to display listing type badge, display name, repo URL, and repo metadata. After the existing lifecycle line (line 51), add rendering for the new fields.

The updated `show` function body (lines 50-66 replacement) should:

1. Show listing type badge after the similarity line: `[SCRAPED]`, `[PUBLIC]`, or nothing for private
2. Show `display_name` from `other_project` if present
3. For scraped projects, show `repo_url` as a clickable link line
4. For scraped projects, render `repo_metadata` fields: stars, license, last commit, contributors, description, topics
5. Keep existing comparison rendering unchanged

After line 51 (`typer.echo(f"Lifecycle: ...")`), add:

```python
    other = match.get("other_project", {})
    lt = match.get("listing_type", "private")

    if lt != "private":
        typer.echo(f"Type: [{lt.upper()}]")
    if other.get("display_name"):
        typer.echo(f"Project: {other['display_name']}")
    if other.get("repo_url"):
        typer.echo(f"Repository: {other['repo_url']}")

    meta = other.get("repo_metadata")
    if meta:
        parts = []
        if meta.get("stars") is not None:
            parts.append(f"{meta['stars']} stars")
        if meta.get("license"):
            parts.append(meta["license"])
        if meta.get("contributor_count") is not None:
            parts.append(f"{meta['contributor_count']} contributors")
        if parts:
            typer.echo(f"  {' · '.join(parts)}")
        if meta.get("description"):
            typer.echo(f"  {meta['description']}")
        if meta.get("topics"):
            typer.echo(f"  Topics: {', '.join(meta['topics'])}")
        if meta.get("last_commit_at"):
            typer.echo(f"  Last commit: {meta['last_commit_at'][:10]}")
        if meta.get("scraped_at"):
            typer.echo(f"  Scraped: {meta['scraped_at'][:10]}")
```

**Testing:**
Tests must verify each AC listed above:
- match-ux-listing-types.AC3.1: Show command displays listing_type, display_name, repo_url
- match-ux-listing-types.AC3.2: Scraped repo match shows stars, license, last commit, contributors, description, topics, scraped_at

Mock response should include a scraped match with full `repo_metadata` and a private match with null `repo_url`/`repo_metadata`. Assert the scraped output includes repo metadata fields; assert the private output does not show `[PRIVATE]` badge or repo metadata.

**Verification:**
Run: `cd /Users/john/codez/our-code/ourcode-plugin && uv run python -m pytest tests/ -v -k "match"`
Expected: All match tests pass

**Commit:** `feat(cli): show repo metadata and listing type badges in match detail view`
<!-- END_TASK_2 -->
<!-- END_SUBCOMPONENT_A -->

<!-- START_SUBCOMPONENT_B (tasks 3-4) -->
<!-- START_TASK_3 -->
### Task 3: Update contact info command to accept structured input

**Verifies:** match-ux-listing-types.AC2.1, match-ux-listing-types.AC2.2, match-ux-listing-types.AC2.3

**Files:**
- Modify: `/Users/john/codez/our-code/ourcode-plugin/src/cli/profile.py:20-29` (set_contact command)

**Implementation:**

Replace the free-text `set-contact` command with one that accepts structured contact methods. The command should accept repeated `--method` options in `type:value` format, a `--preferred` option to mark which type is preferred, optional `--timezone`, and optional `--notes`.

Replace the `set_contact` function (lines 20-29) with:

```python
# Client-side validation only — server is the source of truth.
# If the server adds new types, update this tuple to match.
CONTACT_TYPES = ("email", "discord", "linkedin", "slack", "twitter", "github_discussion", "other")


@app.command("set-contact")
def set_contact(
    method: list[str] = typer.Option(..., "--method", "-m", help="Contact method as type:value (e.g. email:you@example.com)"),
    preferred: str = typer.Option(..., "--preferred", "-p", help="Contact type to mark as preferred"),
    timezone: str = typer.Option(None, "--timezone", "-t", help="IANA timezone (e.g. America/New_York)"),
    notes: str = typer.Option(None, "--notes", "-n", help="Additional notes (max 500 chars)"),
):
    """Set or update your contact info with structured methods."""
    methods = []
    for entry in method:
        if ":" not in entry:
            typer.echo(f"Invalid method format '{entry}'. Use type:value (e.g. email:you@example.com)", err=True)
            raise typer.Exit(code=1)
        ctype, value = entry.split(":", 1)
        ctype = ctype.strip().lower()
        value = value.strip()
        if ctype not in CONTACT_TYPES:
            typer.echo(f"Unknown contact type '{ctype}'. Valid types: {', '.join(CONTACT_TYPES)}", err=True)
            raise typer.Exit(code=1)
        methods.append({"type": ctype, "value": value, "preferred": ctype == preferred.strip().lower()})

    if not any(m["preferred"] for m in methods):
        typer.echo(f"Preferred type '{preferred}' not found in provided methods.", err=True)
        raise typer.Exit(code=1)

    payload: dict = {"methods": methods}
    if timezone:
        payload["timezone"] = timezone
    if notes:
        payload["notes"] = notes

    client = get_client()
    response = client.post("/developers/me/contact-info", json=payload)
    data = response.json()

    typer.echo("Contact info updated:")
    for m in data.get("methods", []):
        pref = " (preferred)" if m.get("preferred") else ""
        typer.echo(f"  {m['type']}: {m['value']}{pref}")
    if data.get("timezone"):
        typer.echo(f"  Timezone: {data['timezone']}")
    if data.get("notes"):
        typer.echo(f"  Notes: {data['notes']}")
```

**Testing:**
Tests must verify each AC listed above:
- match-ux-listing-types.AC2.1: Single method with preferred flag succeeds, output shows method with "(preferred)"
- match-ux-listing-types.AC2.2: Multiple methods with one preferred succeeds
- match-ux-listing-types.AC2.3: All known contact types accepted (test at least email, discord, linkedin)
- Error case: invalid format (no colon) exits with code 1
- Error case: unknown contact type exits with code 1
- Error case: preferred type not in methods exits with code 1

Use `runner.invoke(profile_app, ["set-contact", "-m", "email:a@b.com", "-p", "email"])` pattern.

**Verification:**
Run: `cd /Users/john/codez/our-code/ourcode-plugin && uv run python -m pytest tests/ -v -k "profile"`
Expected: All profile tests pass

**Commit:** `feat(cli): structured contact info input with typed methods`
<!-- END_TASK_3 -->

<!-- START_TASK_4 -->
### Task 4: Update profile show to display contact_method_count

**Verifies:** match-ux-listing-types.AC6.1

**Files:**
- Modify: `/Users/john/codez/our-code/ourcode-plugin/src/cli/profile.py:10-17` (show command)

**Implementation:**

Update the `show` command to display `contact_method_count` from the API response.

Replace lines 10-17:

```python
@app.command()
def show():
    """Show your profile."""
    client = get_client()
    response = client.get("/developers/me")
    data = response.json()
    typer.echo(f"Contact info set: {data['has_contact_info']}")
    if data.get("contact_method_count"):
        typer.echo(f"Contact methods: {data['contact_method_count']}")
    typer.echo(f"Projects: {data['project_count']}")
```

**Testing:**
Tests must verify:
- match-ux-listing-types.AC6.1: Profile show displays `contact_method_count` when present in response

Update the existing `test_profile_show` mock response to include `"contact_method_count": 2` and assert `"Contact methods: 2"` in output.

**Verification:**
Run: `cd /Users/john/codez/our-code/ourcode-plugin && uv run python -m pytest tests/ -v -k "profile"`
Expected: All profile tests pass

**Commit:** `feat(cli): display contact method count in profile`
<!-- END_TASK_4 -->
<!-- END_SUBCOMPONENT_B -->

<!-- START_SUBCOMPONENT_C (tasks 5-6) -->
<!-- START_TASK_5 -->
### Task 5: Update introduction display for structured contact info and auto-approve

**Verifies:** match-ux-listing-types.AC5.2, match-ux-listing-types.AC5.3

**Files:**
- Modify: `/Users/john/codez/our-code/ourcode-plugin/src/cli/client.py` (add format_contact_info helper after get_client)
- Modify: `/Users/john/codez/our-code/ourcode-plugin/src/cli/intros.py:1-4,41-54` (import + accept command)
- Modify: `/Users/john/codez/our-code/ourcode-plugin/src/cli/matches.py:1-5,81-93` (import + connect command)

**Implementation:**

The server now returns structured contact info (methods array with type/value/preferred, timezone, notes) instead of a plain string for both the `connect` (auto-approve for public projects) and `accept` commands. Both need a shared helper to render structured contact info.

Add a helper function in `client.py` (shared by all CLI modules):

In `/Users/john/codez/our-code/ourcode-plugin/src/cli/client.py`, add at the end of the file (after `get_client()`):

```python
def format_contact_info(info):
    """Format structured or plain-text contact info for display.

    Handles both the new structured format (dict with methods array)
    and the legacy plain string format for backwards compatibility.
    """
    if isinstance(info, str):
        return info
    lines = []
    for m in info.get("methods", []):
        pref = " (preferred)" if m.get("preferred") else ""
        lines.append(f"    {m['type']}: {m['value']}{pref}")
    if info.get("timezone"):
        lines.append(f"    Timezone: {info['timezone']}")
    if info.get("notes"):
        lines.append(f"    Notes: {info['notes']}")
    return "\n".join(lines)
```

Update `accept` command in `intros.py` (lines 50-54). Import `format_contact_info` from `cli.client` and replace:

```python
from cli.client import get_client, format_contact_info

# ... in accept():
    typer.echo(f"Introduction accepted: {data['id']}")
    if data.get("requester_contact_info"):
        typer.echo(f"Requester contact info:\n{format_contact_info(data['requester_contact_info'])}")
    if data.get("target_contact_info"):
        typer.echo(f"Your contact info shared:\n{format_contact_info(data['target_contact_info'])}")
```

Update `connect` command in `matches.py` (lines 91-93). Import `format_contact_info` from `cli.client` and replace:

```python
from cli.client import get_client, format_contact_info

# ... in connect():
    typer.echo(f"Introduction {data['status']}: {data['id']}")
    if data.get("target_contact_info"):
        typer.echo(f"Target contact info:\n{format_contact_info(data['target_contact_info'])}")
```

If the auto-approve response includes `status: "accepted"`, the CLI already prints the status correctly. The only change is rendering the structured contact info instead of the plain string.

**Testing:**
Tests must verify:
- match-ux-listing-types.AC5.2: `connect` command with auto-approve response (status=accepted + structured target_contact_info) renders methods array
- match-ux-listing-types.AC5.3: `accept` command with structured contact info renders methods for both parties
- Backwards compat: plain string contact info still renders correctly (isinstance check)

Mock responses should use structured contact objects like `{"methods": [{"type": "email", "value": "alice@example.com", "preferred": true}], "timezone": "America/New_York"}`.

**Verification:**
Run: `cd /Users/john/codez/our-code/ourcode-plugin && uv run python -m pytest tests/ -v -k "intro or connect"`
Expected: All intro/connect tests pass

**Commit:** `feat(cli): render structured contact info in introduction flows`
<!-- END_TASK_5 -->

<!-- START_TASK_6 -->
### Task 6: Update submit command to show listing type for matches

**Verifies:** match-ux-listing-types.AC3.1

**Files:**
- Modify: `/Users/john/codez/our-code/ourcode-plugin/src/cli/projects.py:77-90` (submit match display)

**Implementation:**

Update the match display in the `submit` command to show listing type badge and repo URL for scraped matches. Note: the submit response (`POST /projects`) returns flat match objects (not nested under `other_project` like `GET /projects/{id}/matches`), so `listing_type`, `display_name`, and `repo_url` are read from the top level of each match, consistent with how `lifecycle_stage` and `summary` are already read. After the existing `typer.echo(f"    - {pct}% similar ({stage})")` line (line 86), add:

```python
            lt = m.get("listing_type")
            name = m.get("display_name")
            if lt and lt != "private":
                label = f"[{lt.upper()}]"
                if name:
                    label += f" {name}"
                typer.echo(f"      {label}")
            elif name:
                typer.echo(f"      {name}")
            repo_url = m.get("repo_url")
            if repo_url:
                typer.echo(f"      Repo: {repo_url}")
```

**Testing:**
Tests must verify:
- match-ux-listing-types.AC3.1: Submit output for a scraped match shows `[SCRAPED]` badge, display_name, and repo_url
- Existing test `test_projects_submit_with_matches` still passes (private matches unchanged)

Add a new test with a mixed match response including one scraped match with `listing_type`, `display_name`, and `repo_url` fields. Assert the badge and URL appear in output.

**Verification:**
Run: `cd /Users/john/codez/our-code/ourcode-plugin && uv run python -m pytest tests/ -v -k "submit"`
Expected: All submit tests pass

**Commit:** `feat(cli): show listing type badges in project submit results`
<!-- END_TASK_6 -->
<!-- END_SUBCOMPONENT_C -->

<!-- START_SUBCOMPONENT_D (tasks 7-8) -->
<!-- START_TASK_7 -->
### Task 7: Update ourcode-submit skill documentation

**Verifies:** None (documentation, not testable behavior)

**Files:**
- Modify: `/Users/john/codez/our-code/ourcode-plugin/skills/ourcode-submit/SKILL.md`

**Implementation:**

Update the skill to describe the new match display format with listing types. Changes:

1. **Step 5 match display** (around line 69-90): Add listing type badges to the example output. Scraped matches show `[SCRAPED]` with repo URL instead of match comparison. Private and public matches show comparison as before.

2. **Step 7 contact info** (around line 133-135): Replace the free-text `set-contact` example with structured format:
   ```bash
   ourcode profile set-contact -m email:you@example.com -p email
   ```

3. Add a note after match display explaining the three types:
   - **Private/Public matches**: Human-submitted projects. Request an introduction to connect.
   - **Scraped matches** `[SCRAPED]`: Open-source repos. Visit the repo URL directly — no introduction needed.

**Verification:**
Run: Review the updated SKILL.md reads correctly.

**Commit:** `docs: update ourcode-submit skill for listing types and structured contact info`
<!-- END_TASK_7 -->

<!-- START_TASK_8 -->
### Task 8: Update ourcode-account skill documentation

**Verifies:** None (documentation, not testable behavior)

**Files:**
- Modify: `/Users/john/codez/our-code/ourcode-plugin/skills/ourcode-account/SKILL.md`

**Implementation:**

Update the skill to describe new CLI interfaces:

1. **Profile section** (around line 30-31): Replace the free-text `set-contact` example with structured format:
   ```bash
   # Set structured contact info
   ourcode profile set-contact -m email:you@example.com -m discord:yourname#1234 -p email

   # With timezone and notes
   ourcode profile set-contact -m email:you@example.com -p email -t America/New_York -n "Available evenings"
   ```

2. **Matches section** (around line 49-58): Add the `--type` filter to match list:
   ```bash
   # Filter matches by listing type
   ourcode matches list <project-id> --type scraped
   ```

3. **Matches section**: Add note explaining match types:
   - Matches now include three types: `private`, `public`, and `scraped`
   - Scraped matches are open-source repos — visit the repo URL directly
   - Private/public matches support introductions

4. **Error handling** (around line 101): Update the "target project has introductions blocked" error to mention scraped repos:
   - `"target project has introductions blocked"`: That project cannot receive introductions. If it's a scraped open-source repo, visit the repo URL directly instead.

**Verification:**
Run: Review the updated SKILL.md reads correctly.

**Commit:** `docs: update ourcode-account skill for listing types and structured contact info`
<!-- END_TASK_8 -->
<!-- END_SUBCOMPONENT_D -->
