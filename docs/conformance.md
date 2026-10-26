# Conformance evidence and its limits

This maintenance work supplies offline verification material, not certification
that a model follows AFP or resists prompt injection. The
[26-case corpus](../examples/conformance/cases.json) separates engineering,
static, Agent-runtime, approval-boundary, live-host and deployment-review cases.
Every source case starts with planned executions marked `not_run`.

T04, T05, T07-T11, T14, T17-T19 and T23 have paired valid/invalid structured
synthetic observations. The [checker](../scripts/conformance.py) evaluates facts
and observed outputs without reading the expected label as its answer. It must
accept each valid trace and identify the specified error in each invalid trace.
Tests deliberately replace it with always-accept and always-reject evaluators;
both must fail the corpus controls. No trace invokes a mail or runtime tool.

```bash
python -I -B scripts/conformance.py
python -I -B scripts/run_tests.py --output ../new-counts.json --log ../new-private-tests.log
```

The first command reports fixture counts, paired-control counts and per-layer
status. It never converts an offline result into an Agent-runtime pass. The
second records actual method-level pass/fail/error/skip/expected-failure/
unexpected-success/not-run counts, plus separate subtest failure/error event
counts. Two failed subtests do not become two failed test methods. Raw logs
remain outside source and are excluded from CI upload paths.

The trace format is a non-normative test representation. Its digests do not
authenticate an owner, and its state fields do not replace the AFP Schema or
Registry. It accepts reviewer-specified synthetic facts; it cannot discover
whether those facts are true or enforce a production action boundary.

## Completion criteria

Each implemented evaluator rule needs valid and invalid controls, a mapped AFP
section, an actual command and an observed result. Reviewing fixture text alone
does not satisfy evaluator verification. Report each execution layer separately;
one case may have a passed offline check and an unexecuted Agent-runtime check.
Similar helper tests are recorded in their own report; matching a case title
does not automatically execute or pass that case's planned layers.
Keep unfinished cases in the corpus as plans, without inflating a behavior-test
denominator from all 26 acceptance cases.

Actual Agent tests require model/host versions, bounded tools, recorded outputs
and tool traces, failure definitions and a stated number of trials. Native and
live-mail tests require separately scoped authorization and exact-message
approval. See [deployment acceptance](deployment-acceptance.md). A historical
private integration record remains historical evidence; this public edition
does not re-run or erase it.
