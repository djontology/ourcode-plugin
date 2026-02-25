# Human Test Plan: Match UX Listing Types

## Prerequisites
- Plugin installed locally (`uv pip install -e .`)
- Run `pytest tests/test_commands.py` -- all tests passing
- Access to a running OurCode server (or staging environment)
- A registered developer account with a valid API token (`ourcode auth login`)
- At least one submitted project with matches

## Phase 1: Match Listing Display

| Step | Action | Expected |
|------|--------|----------|
| 1 | Run `ourcode matches list <project-id>` | Output table includes columns: Match ID, Tier, Similarity, Type, Name, Intro Status |
| 2 | Identify a scraped match in the list | Type column shows `scraped`, Name column shows the repository display name |
| 3 | Identify a private match in the list | Type column shows `private`, Name column shows `-` |
| 4 | Run `ourcode matches list <project-id> --type scraped` | Only scraped matches appear in results |
| 5 | Run `ourcode matches list <project-id> --type private` | Only private matches appear in results |

## Phase 2: Match Detail Display

| Step | Action | Expected |
|------|--------|----------|
| 1 | Run `ourcode matches show <scraped-match-id> --project <project-id>` | Output shows `[SCRAPED]` badge, display name as "Project: <name>", and "Repository: https://github.com/..." |
| 2 | In the same output, check repo metadata section | Shows star count, license, contributor count, description, topics list, last commit date, and scraped date |
| 3 | Run `ourcode matches show <private-match-id> --project <project-id>` | No `Repository:` line, no stars/license/contributors metadata |
| 4 | Run `ourcode matches show <public-match-id> --project <project-id>` | Shows `[PUBLIC]` badge |

## Phase 3: Contact Info Management

| Step | Action | Expected |
|------|--------|----------|
| 1 | Run `ourcode profile set-contact -m email:you@test.com -p email` | Output: "Contact info updated:" followed by "email: you@test.com (preferred)" |
| 2 | Run `ourcode profile set-contact -m email:you@test.com -m discord:user#1234 -p email` | Both methods shown, only email marked (preferred) |
| 3 | Run `ourcode profile set-contact -m email:you@test.com -p email -t America/New_York -n "Available evenings"` | Output includes "Timezone: America/New_York" and "Notes: Available evenings" |
| 4 | Run `ourcode profile set-contact -m fax:12345 -p fax` | Exit code 1, output contains "Unknown contact type" |
| 5 | Run `ourcode profile show` | Output includes "Contact methods: 2" (or whatever the current count is) |

## Phase 4: Submit with Listing Types

| Step | Action | Expected |
|------|--------|----------|
| 1 | Run `ourcode projects submit <summary-file>` against a project that has scraped matches | Exact/Partial/Related match sections show `[SCRAPED]` badges, display names, and repo URLs for scraped matches |
| 2 | Check that private matches in submit output | No repo URL shown, no badge displayed |

## Phase 5: Introduction Flow

| Step | Action | Expected |
|------|--------|----------|
| 1 | Run `ourcode matches connect <public-match-id> <project-id>` for a public project match | Response shows "accepted" status with structured contact info: method type, value, (preferred) marker, timezone |
| 2 | Have another user send you an introduction request, then run `ourcode intros accept <intro-id>` | Output shows both parties' contact info with method types, values, preferred markers, timezones, and notes |

## End-to-End: Full Workflow with Scraped Matches

1. Run `ourcode profile set-contact -m email:dev@example.com -m discord:dev#0001 -p email -t US/Eastern`
2. Verify `ourcode profile show` shows "Contact methods: 2"
3. Run `ourcode projects submit summary.json` and note any scraped matches
4. Run `ourcode matches list <project-id> --type scraped` to filter to scraped only
5. Run `ourcode matches show <match-id> --project <project-id>` and verify full repo metadata (stars, license, contributors, topics, dates)
6. Run `ourcode matches connect <match-id> <project-id>` for a public match and verify contact info is returned immediately

## Human Verification Required

| Criterion | Why Manual | Steps |
|-----------|------------|-------|
| Tasks 7-8 (SKILL.md updates) | Documentation-only; no testable CLI behavior | Review `skills/ourcode-account/SKILL.md` and `skills/ourcode-submit/SKILL.md` for accurate listing type documentation |
| Visual formatting of tables/badges | Automated tests check content presence but not readability | Run `ourcode matches list` and `ourcode matches show` in a real terminal; verify columns align, badges are visually distinct |
| Error handling under real network conditions | Mocked tests cannot cover timeouts or server errors | Test with server down, invalid token, and slow connection to verify graceful error messages |

## Traceability

| Acceptance Criterion | Automated Test | Manual Step |
|----------------------|----------------|-------------|
| AC3.1 listing_type in list | `test_matches_list` | Phase 1, Step 1-3 |
| AC3.1 listing_type badge in show | `test_matches_show_with_comparison` | Phase 2, Step 3-4 |
| AC3.1 repo_url in show | `test_matches_show_scraped_with_repo_metadata` | Phase 2, Step 1 |
| AC3.1 display_name in show | `test_matches_show_scraped_with_repo_metadata` | Phase 2, Step 1 |
| AC3.1 submit badges | `test_projects_submit_with_scraped_matches` | Phase 4, Step 1 |
| AC3.2 full repo metadata | `test_matches_show_scraped_with_repo_metadata` | Phase 2, Step 2 |
| AC3.3 private null fields (list) | `test_matches_list_private_no_name` | Phase 1, Step 3 |
| AC3.3 private null fields (show) | `test_match_show_private_no_repo_metadata` | Phase 2, Step 3 |
| AC3.5 listing_type filter | `test_matches_list_with_filter` | Phase 1, Step 4-5 |
| AC3.5 no filter no param | `test_match_list_no_filter_no_query_param` | Phase 1, Step 1 |
| AC2.1 single contact method | `test_profile_set_contact_single_method` | Phase 3, Step 1 |
| AC2.2 multiple methods | `test_profile_set_contact_multiple_methods` | Phase 3, Step 2 |
| AC2.3 all known types | `test_profile_set_contact_all_types` | Phase 3, Step 1-2 |
| AC2.3 unknown type rejected | `test_profile_set_contact_unknown_type` | Phase 3, Step 4 |
| AC5.2 auto-approve connect | `test_matches_connect_with_auto_approve` | Phase 5, Step 1 |
| AC5.3 structured both parties | `test_intros_accept_with_structured_contact_info` | Phase 5, Step 2 |
| AC5.3 legacy compat | `test_intros_accept_with_legacy_contact_info` | -- (automated only) |
| AC6.1 contact_method_count shown | `test_profile_show` | Phase 3, Step 5 |
| AC6.1 count omitted when zero | `test_profile_show_omits_contact_method_count_when_zero` | -- (automated only) |
