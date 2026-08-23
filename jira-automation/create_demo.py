"""
Reads a backlog YAML and creates JIRA tickets.

Flow:
    1. Validate the YAML — warn about over-granular tickets
    2. Ask for confirmation if warnings exist
    3. Create the Epic
    4. Create each Story linked to that Epic
    5. Print a summary with the created issue keys

Usage:
    python create_demo.py
    python create_demo.py requirements/epic-01-auth.yaml
"""

import sys
from jira_client import JiraClient
from validate_backlog import load_and_validate, print_result, confirm_proceed


def create_from_backlog(path: str = "requirements/backlog.yaml"):
    # ----------------------------------------------------------------
    # Step 1 — Validate before touching JIRA
    # ----------------------------------------------------------------
    backlog, validation = load_and_validate(path)
    print_result(validation, path)

    if not validation.passed:
        if not confirm_proceed():
            print("\n  Aborted. Fix the backlog YAML and try again.\n")
            sys.exit(0)

    client = JiraClient()

    print("=" * 55)
    print(f"  Creating tickets from: {path}")
    print("=" * 55)

    # ----------------------------------------------------------------
    # Step 2 — Create the Epic
    # ----------------------------------------------------------------
    epic_data = backlog.get("epic", {})
    print(f"\n[Epic] {epic_data.get('summary')}")

    epic_result = client.create_epic(
        summary=epic_data.get("summary", ""),
        description=epic_data.get("description", ""),
        labels=epic_data.get("labels", []),
    )
    epic_key = epic_result["key"]

    # ----------------------------------------------------------------
    # Step 3 — Create each Story linked to the Epic
    # ----------------------------------------------------------------
    stories = backlog.get("stories", [])
    print(f"\n[Stories] Creating {len(stories)} stories under {epic_key}...")

    created = []
    for story in stories:
        result = client.create_story(
            summary=story.get("summary", ""),
            description=story.get("description", ""),
            epic_key=epic_key,
            priority=story.get("priority", "Medium"),
            labels=story.get("labels", []),
            feature_id=story.get("id"),
        )
        created.append({"id": story.get("id"), "key": result["key"], "summary": story.get("summary")})

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print("\n" + "=" * 55)
    print("  DONE — Tickets created")
    print("=" * 55)
    print(f"\n  Epic  : {epic_key}  —  {epic_data.get('summary')}")
    print("\n  Stories:")
    for item in created:
        print(f"    {item['key']}  [{item['id']}]  {item['summary']}")

    print(f"\n  Open in JIRA: {client.base_url.replace('/rest/api/3', '')}/jira/software/projects/{epic_key.split('-')[0]}/boards")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "requirements/backlog.yaml"
    create_from_backlog(path)
