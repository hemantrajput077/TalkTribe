"""
JIRA REST API v3 client.

Handles authentication and issue creation.
All API calls use Basic Auth: email + API token.
"""

import os
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load from the project root .env, not a local one
load_dotenv(Path(__file__).parent.parent / ".env")

JIRA_URL = os.getenv("JIRA_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")


# Map planning terms → valid JIRA priority names
PRIORITY_MAP = {
    "critical": "Highest",
    "highest": "Highest",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "lowest": "Lowest",
}


class JiraClient:
    def __init__(self):
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY]):
            raise ValueError("Missing JIRA credentials. Fill in .env first.")

        self.base_url = f"{JIRA_URL}/rest/api/3"
        self.auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, json=payload, auth=self.auth, headers=self.headers)
        if not response.ok:
            raise RuntimeError(
                f"JIRA API error {response.status_code}: {response.text}"
            )
        return response.json()

    def _get(self, endpoint: str) -> dict:
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        if not response.ok:
            raise RuntimeError(
                f"JIRA API error {response.status_code}: {response.text}"
            )
        return response.json()

    # ------------------------------------------------------------------
    # Connection check
    # ------------------------------------------------------------------

    def get_myself(self) -> dict:
        """Verify credentials by fetching the authenticated user."""
        return self._get("myself")

    def get_project(self) -> dict:
        """Fetch basic info about the configured JIRA project."""
        return self._get(f"project/{JIRA_PROJECT_KEY}")

    # ------------------------------------------------------------------
    # Issue creation
    # ------------------------------------------------------------------

    def _text_to_adf(self, text: str) -> dict:
        """
        Convert plain text to JIRA's Atlassian Document Format (ADF).
        JIRA REST API v3 requires ADF for description fields — plain strings are rejected.
        """
        paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
        content = []
        for para in paragraphs:
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": para}],
            })
        return {"type": "doc", "version": 1, "content": content}

    def create_epic(self, summary: str, description: str = "", labels: list = None) -> dict:
        """
        Create a JIRA Epic.
        Returns the full API response including the created issue key (e.g. TT-1).
        """
        payload = {
            "fields": {
                "project": {"key": JIRA_PROJECT_KEY},
                "issuetype": {"name": "Epic"},
                "summary": summary,
                "description": self._text_to_adf(description),
                "labels": labels or [],
            }
        }
        result = self._post("issue", payload)
        print(f"  [Epic created]  {result['key']} — {summary}")
        return result

    def create_story(
        self,
        summary: str,
        description: str = "",
        epic_key: str = None,
        priority: str = "Medium",
        labels: list = None,
        feature_id: str = None,
    ) -> dict:
        """
        Create a JIRA Story and link it to an Epic.

        epic_key  — the key returned when you created the Epic (e.g. TT-1).
                    JIRA links Stories to Epics via the 'parent' field in next-gen
                    projects, or 'customfield_10014' in classic projects.
                    We try 'parent' first (works for team-managed projects).
        """
        full_description = description
        if feature_id:
            full_description = f"Feature ID: {feature_id}\n\n{description}"

        jira_priority = PRIORITY_MAP.get(priority.lower(), priority)
        fields = {
            "project": {"key": JIRA_PROJECT_KEY},
            "issuetype": {"name": "Story"},
            "summary": summary,
            "description": self._text_to_adf(full_description),
            "priority": {"name": jira_priority},
            "labels": labels or [],
        }

        if epic_key:
            # Works for team-managed (next-gen) JIRA projects.
            # For company-managed (classic) projects, replace with:
            #   "customfield_10014": epic_key
            fields["parent"] = {"key": epic_key}

        result = self._post("issue", {"fields": fields})
        print(f"  [Story created] {result['key']} — {summary}")
        return result

    def create_task(
        self,
        summary: str,
        description: str = "",
        parent_key: str = None,
        priority: str = "Medium",
        labels: list = None,
    ) -> dict:
        """Create a JIRA Task under a Story (subtask-style)."""
        jira_priority = PRIORITY_MAP.get(priority.lower(), priority)
        fields = {
            "project": {"key": JIRA_PROJECT_KEY},
            "issuetype": {"name": "Task"},
            "summary": summary,
            "description": self._text_to_adf(description),
            "priority": {"name": jira_priority},
            "labels": labels or [],
        }
        if parent_key:
            fields["parent"] = {"key": parent_key}

        result = self._post("issue", {"fields": fields})
        print(f"  [Task created]  {result['key']} — {summary}")
        return result
