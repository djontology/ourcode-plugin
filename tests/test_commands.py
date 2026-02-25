"""Smoke tests for profile, projects, matches, and intros subcommands."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.profile import app as profile_app
from cli.projects import app as projects_app
from cli.matches import app as matches_app
from cli.intros import app as intros_app

runner = CliRunner()


def _mock_client():
    """Return a MagicMock that stands in for APIClient."""
    return MagicMock()


@pytest.fixture(autouse=True)
def _patch_get_client():
    """Patch get_client so no real config or network is needed."""
    client = _mock_client()
    with patch("cli.client.get_client", return_value=client) as mock_gc:
        mock_gc._client = client
        yield client


def _set_response(client, json_data, status_code=200):
    """Configure the mock client's last-called method to return json_data."""
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    client.get.return_value = resp
    client.post.return_value = resp
    client.patch.return_value = resp
    client.delete.return_value = resp
    return resp


# -- profile -------------------------------------------------------------------


def test_profile_show(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {"has_contact_info": True, "project_count": 2, "contact_method_count": 1})

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, ["show"])

    assert result.exit_code == 0
    assert "Contact info set: True" in result.output
    assert "Projects: 2" in result.output
    assert "Contact methods: 1" in result.output


def test_profile_set_contact_single_method(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {
        "methods": [
            {"type": "email", "value": "you@example.com", "preferred": True}
        ]
    })

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, ["set-contact", "-m", "email:you@example.com", "-p", "email"])

    assert result.exit_code == 0
    assert "Contact info updated:" in result.output
    assert "email: you@example.com (preferred)" in result.output
    client.post.assert_called_once()


def test_profile_set_contact_multiple_methods(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {
        "methods": [
            {"type": "email", "value": "you@example.com", "preferred": True},
            {"type": "discord", "value": "yourname#1234", "preferred": False},
            {"type": "linkedin", "value": "https://linkedin.com/in/yourname", "preferred": False}
        ]
    })

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, [
            "set-contact",
            "-m", "email:you@example.com",
            "-m", "discord:yourname#1234",
            "-m", "linkedin:https://linkedin.com/in/yourname",
            "-p", "email"
        ])

    assert result.exit_code == 0
    assert "Contact info updated:" in result.output
    assert "email: you@example.com (preferred)" in result.output
    assert "discord: yourname#1234" in result.output
    assert "linkedin: https://linkedin.com/in/yourname" in result.output


def test_profile_set_contact_all_types(_patch_get_client):
    """Verify all known contact types are accepted."""
    client = _patch_get_client
    _set_response(client, {
        "methods": [
            {"type": "email", "value": "test@example.com", "preferred": True},
            {"type": "slack", "value": "yourname", "preferred": False},
            {"type": "twitter", "value": "@yourname", "preferred": False},
            {"type": "github_discussion", "value": "yourrepo", "preferred": False},
            {"type": "other", "value": "custom_value", "preferred": False}
        ]
    })

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, [
            "set-contact",
            "-m", "email:test@example.com",
            "-m", "slack:yourname",
            "-m", "twitter:@yourname",
            "-m", "github_discussion:yourrepo",
            "-m", "other:custom_value",
            "-p", "email"
        ])

    assert result.exit_code == 0
    assert "slack: yourname" in result.output
    assert "twitter: @yourname" in result.output
    assert "github_discussion: yourrepo" in result.output
    assert "other: custom_value" in result.output


def test_profile_set_contact_with_timezone_and_notes(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {
        "methods": [
            {"type": "email", "value": "you@example.com", "preferred": True}
        ],
        "timezone": "America/New_York",
        "notes": "Available evenings"
    })

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, [
            "set-contact",
            "-m", "email:you@example.com",
            "-p", "email",
            "-t", "America/New_York",
            "-n", "Available evenings"
        ])

    assert result.exit_code == 0
    assert "Contact info updated:" in result.output
    assert "Timezone: America/New_York" in result.output
    assert "Notes: Available evenings" in result.output


def test_profile_set_contact_invalid_format(_patch_get_client):
    client = _patch_get_client

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, [
            "set-contact",
            "-m", "invalid_no_colon",
            "-p", "email"
        ])

    assert result.exit_code == 1
    assert "Invalid method format" in result.output


def test_profile_set_contact_unknown_type(_patch_get_client):
    client = _patch_get_client

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, [
            "set-contact",
            "-m", "email:test@example.com",
            "-m", "unknown_type:value",
            "-p", "email"
        ])

    assert result.exit_code == 1
    assert "Unknown contact type" in result.output


def test_profile_set_contact_preferred_not_found(_patch_get_client):
    client = _patch_get_client

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, [
            "set-contact",
            "-m", "email:test@example.com",
            "-p", "discord"
        ])

    assert result.exit_code == 1
    assert "Preferred type" in result.output
    assert "not found" in result.output


def test_profile_delete_confirmed(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {})

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, ["delete"], input="y\n")

    assert result.exit_code == 0
    assert "Account deleted" in result.output
    client.delete.assert_called_once_with("/developers/me")


# -- projects ------------------------------------------------------------------


def test_projects_list(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {
        "projects": [
            {
                "id": "abc-123",
                "lifecycle_stage": "active",
                "is_registered": True,
                "created_at": "2025-01-15T00:00:00Z",
            }
        ]
    })

    with patch("cli.projects.get_client", return_value=client):
        result = runner.invoke(projects_app, ["list"])

    assert result.exit_code == 0
    assert "abc-123" in result.output
    assert "active" in result.output


def test_projects_list_empty(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {"projects": []})

    with patch("cli.projects.get_client", return_value=client):
        result = runner.invoke(projects_app, ["list"])

    assert result.exit_code == 0
    assert "No projects" in result.output


def test_projects_submit_with_matches(_patch_get_client, tmp_path):
    client = _patch_get_client
    _set_response(client, {
        "id": "proj-new-123",
        "lifecycle_stage": "mvp",
        "is_registered": True,
        "expires_at": None,
        "created_at": "2025-02-01T00:00:00Z",
        "matches": [
            {
                "project_id": "match-proj-1",
                "tier": "exact",
                "similarity": 0.94,
                "lifecycle_stage": "mvp",
                "summary": {
                    "project": {"goals": ["Build a matching service"]},
                    "tech_stack": {"languages": ["Python"], "frameworks": ["FastAPI"]},
                },
            },
            {
                "project_id": "match-proj-2",
                "tier": "partial",
                "similarity": 0.81,
                "lifecycle_stage": "prototype",
                "summary": {
                    "project": {"goals": ["Create discovery platform"]},
                    "tech_stack": {"languages": ["TypeScript"], "frameworks": ["Next.js"]},
                },
            },
        ],
    })

    summary_file = tmp_path / "summary.json"
    summary_file.write_text('{"schema_version": "2.0", "project": {}, "tech_stack": {}}')

    with patch("cli.projects.get_client", return_value=client):
        result = runner.invoke(projects_app, ["submit", str(summary_file)])

    assert result.exit_code == 0
    assert "proj-new-123" in result.output
    assert "Registered" in result.output
    assert "Exact matches" in result.output
    assert "94%" in result.output
    assert "Build a matching service" in result.output
    assert "Partial matches" in result.output
    assert "81%" in result.output
    assert "Create discovery platform" in result.output


def test_projects_submit_no_matches(_patch_get_client, tmp_path):
    client = _patch_get_client
    _set_response(client, {
        "id": "proj-new-456",
        "lifecycle_stage": "prototype",
        "is_registered": False,
        "expires_at": "2025-02-02T00:00:00Z",
        "created_at": "2025-02-01T00:00:00Z",
        "matches": [],
    })

    summary_file = tmp_path / "summary.json"
    summary_file.write_text('{"schema_version": "2.0", "project": {}, "tech_stack": {}}')

    with patch("cli.projects.get_client", return_value=client):
        result = runner.invoke(projects_app, ["submit", str(summary_file), "--no-register"])

    assert result.exit_code == 0
    assert "proj-new-456" in result.output
    assert "Ephemeral" in result.output
    assert "No similar projects" in result.output


# -- matches -------------------------------------------------------------------


def test_matches_list(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {
        "matches": [
            {
                "match_id": "m-1",
                "tier": "exact",
                "similarity": 0.9512,
                "introduction_status": "pending",
                "listing_type": "public",
                "other_project": {"display_name": "Project Alpha"},
            }
        ]
    })

    with patch("cli.matches.get_client", return_value=client):
        result = runner.invoke(matches_app, ["list", "proj-1"])

    assert result.exit_code == 0
    assert "m-1" in result.output
    assert "exact" in result.output
    assert "public" in result.output
    assert "Project Alpha" in result.output


def test_matches_list_with_filter(_patch_get_client):
    """Test that --type filter appends ?listing_type=<value> to the URL."""
    client = _patch_get_client
    _set_response(client, {
        "matches": [
            {
                "match_id": "m-2",
                "tier": "partial",
                "similarity": 0.8,
                "introduction_status": None,
                "listing_type": "scraped",
                "other_project": {"display_name": "Open Source Repo"},
            }
        ]
    })

    with patch("cli.matches.get_client", return_value=client):
        result = runner.invoke(matches_app, ["list", "proj-1", "--type", "scraped"])

    assert result.exit_code == 0
    assert "m-2" in result.output
    assert "scraped" in result.output
    # Verify the URL was called with the filter
    client.get.assert_called_once_with("/projects/proj-1/matches?listing_type=scraped")


def test_matches_list_private_no_name(_patch_get_client):
    """Test that private matches without display_name show '-'."""
    client = _patch_get_client
    _set_response(client, {
        "matches": [
            {
                "match_id": "m-3",
                "tier": "related",
                "similarity": 0.65,
                "introduction_status": None,
                "listing_type": "private",
                "other_project": {},
            }
        ]
    })

    with patch("cli.matches.get_client", return_value=client):
        result = runner.invoke(matches_app, ["list", "proj-1"])

    assert result.exit_code == 0
    assert "private" in result.output
    assert "-" in result.output


def test_matches_show_with_comparison(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {
        "matches": [
            {
                "match_id": "m-1",
                "tier": "exact",
                "similarity": 0.95,
                "listing_type": "public",
                "other_project": {"lifecycle_stage": "active", "display_name": "Project Beta"},
                "comparison": {
                    "your_architecture": "monolith",
                    "their_architecture": "monolith",
                    "architecture_match": True,
                    "your_lifecycle_stage": "active",
                    "their_lifecycle_stage": "active",
                    "shared_goals": ["analytics"],
                    "unique_to_yours": ["ml"],
                    "unique_to_theirs": [],
                    "shared_languages": ["python"],
                    "unique_languages_yours": [],
                    "unique_languages_theirs": ["rust"],
                    "shared_frameworks": ["fastapi"],
                    "unique_frameworks_yours": [],
                    "unique_frameworks_theirs": [],
                    "shared_libraries": [],
                    "unique_libraries_yours": [],
                    "unique_libraries_theirs": [],
                },
            }
        ]
    })

    with patch("cli.matches.get_client", return_value=client):
        result = runner.invoke(matches_app, ["show", "m-1", "--project", "proj-1"])

    assert result.exit_code == 0
    assert "95%" in result.output
    assert "monolith" in result.output
    assert "analytics" in result.output
    assert "[PUBLIC]" in result.output
    assert "Project Beta" in result.output


def test_matches_show_scraped_with_repo_metadata(_patch_get_client):
    """Test that scraped matches show listing type badge and repo metadata."""
    client = _patch_get_client
    _set_response(client, {
        "matches": [
            {
                "match_id": "m-2",
                "tier": "partial",
                "similarity": 0.82,
                "listing_type": "scraped",
                "other_project": {
                    "lifecycle_stage": "active",
                    "display_name": "Open Source Project",
                    "repo_url": "https://github.com/example/project",
                    "repo_metadata": {
                        "stars": 1250,
                        "license": "MIT",
                        "contributor_count": 45,
                        "description": "An amazing open source project",
                        "topics": ["python", "api", "database"],
                        "last_commit_at": "2025-02-24T10:30:00Z",
                        "scraped_at": "2025-02-24T15:00:00Z"
                    }
                },
                "comparison": {
                    "your_architecture": "microservices",
                    "their_architecture": "monolith",
                    "architecture_match": False,
                    "your_lifecycle_stage": "mvp",
                    "their_lifecycle_stage": "active",
                    "shared_goals": ["api"],
                    "unique_to_yours": [],
                    "unique_to_theirs": [],
                    "shared_languages": ["python"],
                    "unique_languages_yours": [],
                    "unique_languages_theirs": [],
                    "shared_frameworks": [],
                    "unique_frameworks_yours": [],
                    "unique_frameworks_theirs": [],
                    "shared_libraries": [],
                    "unique_libraries_yours": [],
                    "unique_libraries_theirs": [],
                },
            }
        ]
    })

    with patch("cli.matches.get_client", return_value=client):
        result = runner.invoke(matches_app, ["show", "m-2", "--project", "proj-1"])

    assert result.exit_code == 0
    assert "[SCRAPED]" in result.output
    assert "Open Source Project" in result.output
    assert "https://github.com/example/project" in result.output
    assert "1250 stars" in result.output
    assert "MIT" in result.output
    assert "45 contributors" in result.output
    assert "An amazing open source project" in result.output
    assert "python" in result.output
    assert "2025-02-24" in result.output


def test_matches_show_not_found(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {"matches": []})

    with patch("cli.matches.get_client", return_value=client):
        result = runner.invoke(matches_app, ["show", "m-999", "--project", "proj-1"])

    assert result.exit_code == 1
    assert "not found" in result.output.lower()


# -- intros --------------------------------------------------------------------


def test_intros_list(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {
        "incoming": [
            {"id": "i-1", "status": "pending", "created_at": "2025-01-10T00:00:00Z"}
        ],
        "outgoing": [
            {"id": "i-2", "status": "accepted", "created_at": "2025-01-11T00:00:00Z"}
        ],
    })

    with patch("cli.intros.get_client", return_value=client):
        result = runner.invoke(intros_app, ["list"])

    assert result.exit_code == 0
    assert "Incoming" in result.output
    assert "i-1" in result.output
    assert "Outgoing" in result.output
    assert "i-2" in result.output


def test_intros_accept(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {
        "id": "i-1",
        "status": "accepted",
        "requester_contact_info": "alice@example.com",
        "target_contact_info": "bob@example.com",
    })

    with patch("cli.intros.get_client", return_value=client):
        result = runner.invoke(intros_app, ["accept", "i-1"])

    assert result.exit_code == 0
    assert "accepted" in result.output.lower()
    assert "alice@example.com" in result.output


def test_intros_decline(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {"id": "i-1", "status": "declined"})

    with patch("cli.intros.get_client", return_value=client):
        result = runner.invoke(intros_app, ["decline", "i-1"])

    assert result.exit_code == 0
    assert "declined" in result.output.lower()
