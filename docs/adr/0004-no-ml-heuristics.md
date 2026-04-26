# ADR-0004: Heuristic rule-based detection, no machine learning

- Status: Accepted
- Source: `deliverables/warden-architecture.tex:904`

## Context

The detector needs to identify three specific, well-defined attack signatures. An ML approach was considered to allow generalization to unseen variants.

## Decision

Detection is implemented as deterministic, sliding-window heuristics. No ML model is trained or loaded.

## Consequences

- Detection rules are fully auditable and explainable - required for the academic evaluation.
- No training data collection or model management overhead.
- The system will not generalize to attack variants that differ significantly from the defined signatures; that is acceptable for the lab scope.
- If generalization becomes a requirement in a future iteration, this decision can be revisited.
