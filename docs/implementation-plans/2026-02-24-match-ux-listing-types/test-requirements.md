# Phase 6 Test Requirements: Plugin & CLI Updates

## Overview

All tests target the existing test file at `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py` using `typer.testing.CliRunner` with mocked API responses (no live server). Tests follow the established `_mock_client` / `_set_response` pattern in that file.

---

## AC3.1 — Match results include `listing_type`, `display_name`, `repo_url`, `repo_metadata` fields

**Criterion (verbatim):** "Match results include `listing_type`, `display_name`, `repo_url`, `repo_metadata` fields"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_match_list_shows_listing_type_column` | `list` command output contains a `Type` column header and the listing_type value (e.g. `scraped`) for each match row |
| `test_match_list_shows_display_name` | `list` command output includes `display_name` from `other_project` in the Name column |
| `test_match_show_displays_listing_type_badge` | `show` command output includes `[SCRAPED]` or `[PUBLIC]` badge for non-private matches |
| `test_match_show_displays_repo_url` | `show` command output includes `Repository: https://github.com/...` for scraped match |
| `test_match_show_displays_display_name` | `show` command output includes `Project: <display_name>` when present |
| `test_submit_shows_listing_type_badge` | `submit` command output includes `[SCRAPED]` badge and repo URL for scraped matches in results |

---

## AC3.2 — Scraped repo matches show full repo metadata

**Criterion (verbatim):** "Scraped repo matches show full repo metadata (stars, license, last commit, contributors, scraped_at)"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_match_show_scraped_repo_metadata` | `show` command with scraped match response containing full `repo_metadata` outputs: star count, license, contributor count, description, topics, last_commit_at date, and scraped_at date |

---

## AC3.3 — Private project matches have null `repo_url` and `repo_metadata`

**Criterion (verbatim):** "Private project matches have null `repo_url` and `repo_metadata`"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_match_list_private_shows_dash_for_name` | `list` command output shows `-` in Name column when `display_name` is null |
| `test_match_show_private_no_repo_metadata` | `show` command with private match (null `repo_url`, null `repo_metadata`) does not output `Repository:`, star count, license, or any repo metadata lines |

---

## AC3.5 — Optional `?listing_type=scraped` filter returns only scraped matches

**Criterion (verbatim):** "Optional `?listing_type=scraped` filter returns only scraped matches"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_match_list_type_filter_appends_query_param` | Invoking `list <project-id> --type scraped` causes `client.get` to be called with URL containing `?listing_type=scraped` |
| `test_match_list_no_filter_no_query_param` | Invoking `list <project-id>` without `--type` calls `client.get` with URL that does not contain `listing_type` |

---

## AC2.1 — Contact info with one method marked preferred validates and stores correctly

**Criterion (verbatim):** "Contact info with one method marked preferred validates and stores correctly"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_set_contact_single_method` | `set-contact -m email:a@b.com -p email` succeeds (exit code 0), sends POST with `{"methods": [{"type": "email", "value": "a@b.com", "preferred": true}]}`, and output contains `email: a@b.com (preferred)` |

---

## AC2.2 — Contact info with multiple methods (one preferred) validates

**Criterion (verbatim):** "Contact info with multiple methods (one preferred) validates"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_set_contact_multiple_methods` | `set-contact -m email:a@b.com -m discord:user#1234 -p email` succeeds, sends POST with two methods (email preferred=true, discord preferred=false), output shows both methods with only email marked `(preferred)` |

---

## AC2.3 — All known contact types accepted

**Criterion (verbatim):** "All known contact types accepted (`email`, `discord`, `linkedin`, `slack`, `twitter`, `github_discussion`, `other`)"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_set_contact_all_known_types` | For each type in (`email`, `discord`, `linkedin`, `slack`, `twitter`, `github_discussion`, `other`), invoking `set-contact -m <type>:val -p <type>` exits with code 0 (client-side validation passes) |
| `test_set_contact_unknown_type_rejected` | `set-contact -m fax:12345 -p fax` exits with code 1 and stderr contains `Unknown contact type` |

---

## AC5.2 — Introduction to public project auto-approves

**Criterion (verbatim):** "Introduction to public project auto-approves (status = accepted, contact info returned immediately)"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_connect_auto_approve_shows_contact_info` | `connect` command with mocked response `{"id": "...", "status": "accepted", "target_contact_info": {"methods": [{"type": "email", "value": "alice@x.com", "preferred": true}], "timezone": "America/New_York"}}` outputs `accepted`, `email: alice@x.com (preferred)`, and `Timezone: America/New_York` |

---

## AC5.3 — Accepted introduction returns structured contact info for both parties

**Criterion (verbatim):** "Accepted introduction returns structured contact info (methods array, timezone, notes) for both parties"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_accept_intro_shows_structured_contact_both_parties` | `accept` command with mocked response containing `requester_contact_info` and `target_contact_info` (both structured with methods, timezone, notes) outputs contact details for both parties including method types, values, preferred markers, timezone, and notes |
| `test_accept_intro_backwards_compat_plain_string` | `accept` command with plain string `requester_contact_info` (legacy format) renders the string directly without error |

---

## AC6.1 — Profile `contact_method_count`

**Criterion (verbatim):** "`GET /developers/me` returns `contact_method_count` reflecting number of stored methods"

**Test type:** Unit (CliRunner with mocked API)

**Test file:** `/Users/john/codez/our-code/ourcode-plugin/tests/test_commands.py`

**Tests:**

| Test name | Asserts |
|-----------|---------|
| `test_profile_show_displays_contact_method_count` | `show` command with mocked response `{"has_contact_info": true, "contact_method_count": 3, "project_count": 1}` outputs `Contact methods: 3` |
| `test_profile_show_omits_contact_method_count_when_zero` | `show` command with `"contact_method_count": 0` (or absent) does not output `Contact methods:` line |

---

## Criteria not requiring automated tests

| Criterion | Justification |
|-----------|---------------|
| Tasks 7-8 (SKILL.md updates) | Documentation-only changes. No testable CLI behavior. Verified by human review of markdown content. |
