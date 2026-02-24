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
    _set_response(client, {"has_contact_info": True, "project_count": 2})

    with patch("cli.profile.get_client", return_value=client):
        result = runner.invoke(profile_app, ["show"])

    assert result.exit_code == 0
    assert "Contact info set: True" in result.output
    assert "Projects: 2" in result.output


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
            }
        ]
    })

    with patch("cli.matches.get_client", return_value=client):
        result = runner.invoke(matches_app, ["list", "proj-1"])

    assert result.exit_code == 0
    assert "m-1" in result.output
    assert "exact" in result.output


def test_matches_show_with_comparison(_patch_get_client):
    client = _patch_get_client
    _set_response(client, {
        "matches": [
            {
                "match_id": "m-1",
                "tier": "exact",
                "similarity": 0.95,
                "other_project": {"lifecycle_stage": "active"},
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
