"""
Backlog validator — runs before any JIRA tickets are created.

Rules enforced:
  1. Epic must not have more than MAX_STORIES stories.
  2. Every story description must be long enough to be a real story (not a single task).
  3. Stories that share all the same dependencies should be grouped into one.
  4. Story summaries that look like single micro-tasks are flagged.

Usage (standalone):
    python validate_backlog.py requirements/epic-01-auth.yaml

Usage (called by create_demo.py):
    from validate_backlog import validate, ValidationResult
"""

import sys
import yaml
from dataclasses import dataclass, field

# ── Thresholds (adjust to taste) ──────────────────────────────────────────────
MAX_STORIES = 6           # warn if an epic has more than this many stories
MIN_DESC_WORDS = 30       # warn if a story description has fewer words than this
MAX_SHARED_DEPS = 2       # warn if 3+ stories share identical dependency sets

# Words that suggest a summary describes a single micro-task, not a user story
MICRO_TASK_VERBS = {
    "add", "remove", "delete", "rename", "move", "fix", "update", "change",
    "refactor", "create", "drop", "migrate",
}
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class Warning:
    rule: str
    story_id: str
    message: str
    suggestion: str


@dataclass
class ValidationResult:
    warnings: list[Warning] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    def add(self, rule: str, story_id: str, message: str, suggestion: str):
        self.warnings.append(Warning(rule, story_id, message, suggestion))


def validate(backlog: dict) -> ValidationResult:
    result = ValidationResult()
    stories = backlog.get("stories", [])
    epic_summary = backlog.get("epic", {}).get("summary", "Epic")

    # ── Rule 1: Too many stories ───────────────────────────────────────────────
    if len(stories) > MAX_STORIES:
        result.add(
            rule="R1:too-many-stories",
            story_id="EPIC",
            message=(
                f"{epic_summary} has {len(stories)} stories — more than the "
                f"recommended max of {MAX_STORIES}."
            ),
            suggestion=(
                "Group small related stories into one. Each story should represent "
                "roughly one PR's worth of work. Use bullet points inside the "
                "description for individual steps instead of separate stories."
            ),
        )

    dep_groups: dict[str, list[str]] = {}

    for story in stories:
        sid = story.get("id", "?")
        summary = story.get("summary", "")
        description = story.get("description", "")
        deps = tuple(sorted(story.get("dependencies", [])))

        # ── Rule 2: Description too short ─────────────────────────────────────
        word_count = len(description.split())
        if word_count < MIN_DESC_WORDS:
            result.add(
                rule="R2:description-too-short",
                story_id=sid,
                message=(
                    f"[{sid}] description has only {word_count} words "
                    f"(minimum {MIN_DESC_WORDS}). This looks like a task, not a story."
                ),
                suggestion=(
                    "A story needs: user/system story, in scope, out of scope, "
                    "acceptance criteria, and dependencies. If it cannot fill those "
                    "sections, merge it into a related story."
                ),
            )

        # ── Rule 3: Micro-task summary ────────────────────────────────────────
        first_word = summary.strip().lower().split()[0] if summary.strip() else ""
        rest_of_summary = " ".join(summary.strip().split()[1:])
        # Flag only if the summary is short AND starts with a micro-task verb
        if first_word in MICRO_TASK_VERBS and len(summary.split()) <= 6:
            result.add(
                rule="R3:micro-task-summary",
                story_id=sid,
                message=(
                    f"[{sid}] summary '{summary}' looks like a single task "
                    f"(starts with '{first_word}', only {len(summary.split())} words)."
                ),
                suggestion=(
                    "Story summaries should describe observable behavior or a "
                    "meaningful outcome, not a single action. Example: instead of "
                    f"'{summary}', write something like "
                    f"'[Domain] supports [capability] so that [outcome]'. "
                    "If it truly is just a small task, put it as a bullet point "
                    "inside a larger story's description."
                ),
            )

        # ── Rule 4: Dependency clustering (collect for analysis) ──────────────
        if deps:
            key = str(deps)
            dep_groups.setdefault(key, []).append(sid)

    # Evaluate dependency clusters after all stories are processed
    for dep_key, story_ids in dep_groups.items():
        if len(story_ids) > MAX_SHARED_DEPS:
            result.add(
                rule="R4:shared-dependencies",
                story_id=", ".join(story_ids),
                message=(
                    f"Stories {story_ids} all share the same dependencies {dep_key}. "
                    f"This often means they should be one story with multiple tasks."
                ),
                suggestion=(
                    "When multiple stories are blocked by the same things and deliver "
                    "related changes, group them into one story. List the individual "
                    "steps (model, migration, service, API) in the description instead."
                ),
            )

    return result


def print_result(result: ValidationResult, path: str):
    if result.passed:
        print(f"\n  [OK] {path} passed all validation rules. No issues found.\n")
        return

    print(f"\n  {'-' * 55}")
    print(f"  BACKLOG WARNINGS -- {path}")
    print(f"  {'-' * 55}")
    print(f"  {len(result.warnings)} issue(s) found:\n")

    for i, w in enumerate(result.warnings, 1):
        print(f"  [{i}] Rule: {w.rule}")
        print(f"      Story : {w.story_id}")
        print(f"      Issue : {w.message}")
        print(f"      Fix   : {w.suggestion}")
        print()

    print(
        "  These warnings mean your backlog may have too many small tickets.\n"
        "  Smaller tickets = more JIRA overhead, less focus.\n"
        "  Consider grouping before creating.\n"
    )


def confirm_proceed() -> bool:
    """Ask the user whether to create tickets despite warnings."""
    answer = input("  Proceed with ticket creation anyway? (y/n): ").strip().lower()
    return answer == "y"


def load_and_validate(path: str) -> tuple[dict, ValidationResult]:
    with open(path, "r", encoding="utf-8") as f:
        backlog = yaml.safe_load(f)
    result = validate(backlog)
    return backlog, result


# ── Standalone usage ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "requirements/backlog.yaml"
    backlog, result = load_and_validate(path)
    print_result(result, path)
    sys.exit(0 if result.passed else 1)
