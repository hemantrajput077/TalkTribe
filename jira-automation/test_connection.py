"""
Run this first — before creating any tickets.

Verifies:
  1. Your .env credentials are loaded correctly
  2. JIRA accepts your API token
  3. Your project key exists and is accessible

Usage:
    python test_connection.py
"""

from jira_client import JiraClient, JIRA_URL, JIRA_EMAIL, JIRA_PROJECT_KEY


def main():
    print("=" * 50)
    print("  TalkTribe JIRA — Connection Test")
    print("=" * 50)

    # Show what credentials are loaded (never print the token itself)
    print(f"\nJIRA URL      : {JIRA_URL}")
    print(f"Email         : {JIRA_EMAIL}")
    print(f"Project Key   : {JIRA_PROJECT_KEY}")
    print(f"API Token     : {'*' * 20} (hidden)")

    client = JiraClient()

    # Step 1: verify auth by fetching the logged-in user
    print("\n[1] Checking authentication...")
    me = client.get_myself()
    print(f"    Logged in as: {me.get('displayName')} ({me.get('emailAddress')})")

    # Step 2: verify the project exists
    print(f"\n[2] Checking project '{JIRA_PROJECT_KEY}'...")
    project = client.get_project()
    print(f"    Project found: {project.get('name')} ({project.get('key')})")
    print(f"    Project type : {project.get('projectTypeKey')}")

    print("\n[OK] Connection successful. You are ready to create tickets.")
    print("=" * 50)


if __name__ == "__main__":
    main()
