# Evaluation protocol

## Hypothesis

Externally validated lessons generated from prior incidents improve diagnosis on unseen variants, at a fixed model and tool configuration, relative to fresh context and raw experience history.

## v0.1 procedure

1. Use three authored training incidents; collect an attempt and external feedback.
2. Ask the same configured model to propose a lesson and scope.
3. Validate each lesson on one separate family-matched incident.
4. Freeze promoted memory and training history before the test phase.
5. Compare all configurations on the same four test tasks using new Letta agents.
6. Count wrong answers, API errors, and malformed outputs as unsuccessful trials.
7. Preserve individual decisions, revision records, usage, timestamps, and model ID.

The comparator sees action names and task descriptions, never the scorer's answer key. Validation keys are used by the external harness. Held-out results cannot change memory in this run.

## Metrics implemented

Correct action count, exact-choice accuracy, error count, wall-clock latency, and provider-reported usage per decision. Latency includes agent creation. Reflection and validation events are logged; reflection usage is not currently included in aggregate costs. A failed result is not an abstention metric.

## Before making research claims

- Predefine and lock a substantially larger held-out set, with ambiguous and out-of-distribution incidents.
- Make more than one variant per failure family; hold out task templates, not just wording.
- Compare a common cold-start evaluation with subsequent memory checkpoints.
- Add shuffled-memory and irrelevant-memory controls; fix or match context budgets.
- Test contradictory reviewer feedback, stale lessons, and false generalizations.
- Record SDK/server versions, prompt and dataset hashes, model configuration, cost, and seeds where supported.
- Report per-family results and uncertainty across independent tasks; do not treat repeated calls as independent task diversity.
- Check whether performance changes because of memory contents or merely more inference/context.
- Include the cost of reflection, validation, memory maintenance, and human review.

## Boundaries

MemGPT provides a memory-management foundation, not a guarantee that reflection is correct. Letta provides the agent runtime. This repository implements a bounded application-level promotion and evaluation loop. It does not claim a new memory algorithm or novelty over prior work.
