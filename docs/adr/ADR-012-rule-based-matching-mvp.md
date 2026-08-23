# ADR-012: Use Rule-Based Matching for MVP

**Status:** Accepted

## Context

TalkTribe needs to suggest compatible co-learners based on profile information such as interests, hobbies, profession, language, and proficiency. AI-based matching is a future goal.

## Decision

MVP matching will be **deterministic/rule-based**.

The matching system may consider:

- English-language compatibility
- proficiency
- interests
- hobbies
- profession
- block/eligibility state

It returns up to 20 candidate suggestions.

## Alternatives Considered

### Embedding/AI matching
Deferred because it adds model, evaluation, infrastructure, and explainability complexity before the core experience is validated.

### Random matching only
Rejected because TalkTribe explicitly wants similar interests/hobbies/profession to influence compatibility.

## Consequences

### Positive
- Easy to test
- Easy to explain
- Low cost
- Fast to implement
- Creates a baseline against which AI matching can later be evaluated

### Negative
- Less adaptive than AI
- Matching quality depends on manually designed rules

## Future

AI/embedding-based matching may replace or augment the scoring engine without changing the overall Matching domain boundary.
