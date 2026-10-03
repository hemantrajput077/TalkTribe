from __future__ import annotations
from app.domains.matching.application.profile_matching_reader import CandidateSummary

_MAX_INTEREST_SCORE: int = 60
_MAX_PROFESSION_SCORE: int = 20
_MAX_PROFICIENCY_SCORE: int = 20

_CEFR_ORDER: list[str] = ["A1", "A2", "B1", "B2", "C1", "C2"]
_CEFR_INDEX: dict[str, int] = {level: i for i, level in enumerate(_CEFR_ORDER)}


def _interest_score(requester_ids: set[int], candidate_ids: set[int]) -> int:
    if not requester_ids:
        return 0
    shared = len(requester_ids & candidate_ids)
    return round((shared / len(requester_ids)) * _MAX_INTEREST_SCORE)


def _profession_score(requester_profession: str | None, candidate_profession: str | None) -> int:
    if not requester_profession or not candidate_profession:
        return 0
    if requester_profession.strip().lower() == candidate_profession.strip().lower():
        return _MAX_PROFESSION_SCORE
    return 0


def _proficiency_score(requester_level: str | None, candidate_level: str | None) -> int:
    if not requester_level or not candidate_level:
        return 0
    req_idx = _CEFR_INDEX.get(requester_level.upper())
    cand_idx = _CEFR_INDEX.get(candidate_level.upper())
    if req_idx is None or cand_idx is None:
        return 0
    distance = abs(req_idx - cand_idx)
    max_distance = len(_CEFR_ORDER) - 1
    step = _MAX_PROFICIENCY_SCORE / max_distance
    return max(0, round(_MAX_PROFICIENCY_SCORE - distance * step))


def score_candidate(
    requester_interest_ids: set[int],
    requester_profession: str | None,
    requester_proficiency: str | None,
    candidate: CandidateSummary,
) -> int:
    return (
        _interest_score(requester_interest_ids, candidate.interest_ids)
        + _profession_score(requester_profession, candidate.profession)
        + _proficiency_score(requester_proficiency, candidate.proficiency_level)
    )
