from __future__ import annotations

"""
BLOCK-01 — InteractionEligibility contract.

This is the ONLY surface the Matching domain uses to check whether two users are
allowed to appear in each other's recommendations.

Rules (matching.md §8):
  - If A blocked B → A and B must not be recommended to each other.
  - If B blocked A → same.

The Friendship/Block domain will provide a concrete implementation when BLOCK-01
is fully built.  Until then, NullInteractionEligibility is used, which passes
all pairs — correct because no block relationships exist yet.

Matching must NEVER import FriendshipRepository or any block-infrastructure class
directly.  It must always go through this contract (ADR-009, matching.md §8).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class InteractionEligibility(Protocol):
    """
    Contract surface consumed by the Matching (and future Pairing) domain.

    Satisfied by NullInteractionEligibility until BLOCK-01 is implemented.
    """

    async def are_interaction_eligible(self, user_a_id: int, user_b_id: int) -> bool:
        """
        Return True when user_a and user_b may appear in each other's match list.

        Returns False if either user has blocked the other.
        """
        ...


class NullInteractionEligibility:
    """
    BLOCK-01 stub — always permits interaction.

    Replace with a real implementation once the Friendship/Block domain has
    persistent block tables and the BLOCK-01 ticket is complete.
    """

    async def are_interaction_eligible(
        self,
        user_a_id: int,  # noqa: ARG002
        user_b_id: int,  # noqa: ARG002
    ) -> bool:
        """No block tables exist yet — all pairs are eligible."""
        return True
