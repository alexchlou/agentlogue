# ADR 0001: optional claim-to-evidence sidecar

Status: proposed; no Schema or protocol migration.

AFP v1.3 already requires the current observer, material actually read,
association and support scope. Its optional summary has a single evidence
object and human-readable claim lists. Complex automated consumers might need
explicit claim IDs, evidence IDs, observers and support edges.

Option A retains the current text-first representation, with low maintenance
cost and manual review. Option B adds an independently versioned, non-normative
sidecar, with explicit parser/validation and compatibility costs. Neither can
prove a claim true. Repeated retellings of one receipt remain one underlying
source, not independent corroboration. Actual earlier access and later inability
to re-open the original must both be representable.

Do not change existing enums/required fields or old records. Before adopting B,
show a real consumer need, test examples with different observers and support
scopes, define text-conflict holds and obtain a separate compatibility decision.
The conformance corpus provides material for discussion, not a prerequisite
blocking this ADR or an implemented consumer.
