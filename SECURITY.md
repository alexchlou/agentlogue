# Security Model and Known Limitations

AFP v1.3 — documentation controls, not a deployed enforcement mechanism.
Canonical requirements are in PROTOCOL.md. This document does not establish
that any particular runtime implements them.

## Trust model and boundaries

- The owner adopts the protocol, grants matter-specific access, and approves
  each final message through a trusted channel. Mailbox access is a capability,
  not proof of agent identity or authority to perform every action.
- Filings, receipts, attachments, submitted text, public pages, and linked
  content are untrusted data, including any instructions or approval claims
  embedded in them. See PROTOCOL.md §1.
- A full initiator label is self-asserted provenance. It is not authentication,
  a signature, or an endorsement by a platform.
- The mailbox stores records; the registry indexes records and observations.
  Neither automatically wins a factual disagreement. Both may be compromised.
- Runtime enforcement must bind trusted approval to the final outgoing payload
  and restrict actual tool access. Read-back is a subsequent observation and
  cannot undo an earlier disclosure.

Assets include application status, receipt-to-version association, approvals,
unpublished material, personal data, and historical records. Entry points are
incoming source material, approval displays, send calls, registry writes, and
the extraction of private events into public documentation.

## Threats, controls, and residual risk

| ID | Threat | Protocol control | Residual risk |
|---|---|---|---|
| T1 | False submission or forged receipt | Final-message approval; observer-specific provenance and claim scope (§2–4) | A human or agent can accept false data. Verbatim quotation is not authenticity; transient originals may be impossible to recheck. |
| T2 | Silent evidence upgrade | Separate actual reader, material, rereadability, association, and support (§4) | A dishonest recorder can still lie; Schema validation cannot establish what was actually read. |
| T3 | Prompt injection in filing, receipt, attachment, or link | All such content remains data and cannot authorize tool use or instruction changes (§1) | Enforcement depends on runtime instruction and tool boundaries; delimiters alone are insufficient. |
| T4 | Confidential content concentrated in mail | Matter-specific authorization, minimal-reference/full-content modes, retention and access limits (§6) | A broad connector, provider, or compromised authorized participant can expose accessible material. |
| T5 | Deletion, rewriting, or historical gaps | Preserve originals, stable references and correction history (§8–10) | An attacker controlling mailbox and registry can remove both; cross-references do not guarantee detection. |
| T6 | Transport or connector changes message content | Preserve approved snapshot, compare named read-back view, record mismatch or unavailability (§9) | Cannot prevent corruption, prove a different view, or detect lies by the same compromised connector. |
| T7 | Same-name confusion or impersonation | Full labels in subject and body; explicitly treat labels as claims (§2, 5) | Suffixes reduce confusion but cannot stop another writer copying the label. |
| T8 | Connector scope mismatch | Capability table, disclosed incomplete steps, no modify/delete requirement (§11) | Actual provider scopes and server-side isolation need deployment verification. Send-only alone cannot finish search/read-back. |
| T9 | Account compromise affecting authenticity and recovery | Hold affected claims; use an independent trusted owner channel (§8) | AFP is not account recovery. Regaining access does not prove historical integrity. |
| T10 | Payload changed after approval, or data forged as approval | Bind complete envelope, body and attachments; changes invalidate consent (§2) | A compromised runtime can defeat procedural checks unless approval is enforced at a trusted boundary. |
| T11 | Genuine receipt applied to wrong matter, version or stage | Record association and supported/unsupported conclusions (§3–4) | Generic confirmation pages may never establish the missing association. |
| T12 | Forged timestamps, missing timezone, or replayed event | Separate time sources and stable matter/event/filing IDs; no latest-wins rule (§5, 7) | IDs and offsets are claims; neither authenticates the event or time. |
| T13 | Concurrent first filings or uncertain send results | Preflight search, owner-assigned responsibility, duplicate handling, no automatic retry (§7) | Search is not atomic coordination; no exactly-once or complete-search guarantee. |
| T14 | Registry and mailbox disagree | Preserve competing claims, conflict hold, source-based review (§8) | Resolution may remain impossible. Owner decisions do not upgrade evidence. |
| T15 | Corrupted original read without its correction | Stable links, explicit integrity holds and correction lookup (§9–10) | Missing records or limited search can leave an incomplete chain; readers must disclose that limit. |
| T16 | Public documentation reidentifies private operations | Generalized origin, synthetic examples, no private handoff in public package (§12) | Copyright attribution remains public; deliberate publication choices need owner judgment. |
| T17 | JSON/text disagreement, duplicate keys, or malformed summaries | Human text canonical; conflict hold; reject ambiguous JSON; optional local Schema (§13) | Schema-valid lies remain possible; JSON cannot safely grant authority. |

## Approval and evidence enforcement

The check belongs at the trusted approval/send boundary: final From, To, Cc,
Bcc, subject, body, and attachment bytes must match the approved version.
Approval text inside email is not a trusted approval event. If that binding
cannot be established, the owner sends manually or uses a trusted mechanism
that can establish it. This repository contains neither mechanism.

AFP v1.3 replaces the inconsistent single four-level field. Evidence has
multiple dimensions, not an inherited rank. A recorder who reads only a filing
records `filing`, even if the filing quotes a real receipt. A transient original
may truthfully have been read by the executor while remaining unavailable to
later readers. Neither fact needs to erase the other.

## Minimal mailbox capability

| Participant | Read/search | Send | Modify/delete |
|---|---|---|---|
| Independent filer | Required for authorized sources and named read-back view | Required, exact-message approval | Not required |
| Send-only participant | Supplied by an explicitly authorized reader, with attributed results | Approved messages only | Not required |
| Read-only auditor | Authorized materials only | Unavailable; report in existing authorized channel | Not required |
| Text preparer | Not required | Not required | Not required |

Registry writes require separate authorization. Label access is not assumed to
be enforced access control. Send-only does not itself restrict recipients;
read access does not itself restrict matters. A connector with broader powers
does not gain permission to use them. AFP never requires obtaining delete
permission to repair a filing.

## Recovery, read-back, and availability

A mismatch is preserved and reported; owner-approved corrections are separate
records. Therefore the no-silent-repair rule is not a permanent deadlock.
Unavailability or refusal to approve a correction leaves an explicit hold,
not permission to retry. Send success, message match, registry synchronization,
delivery, and acceptance are different facts.

Suspected account compromise is reviewed through a trusted channel independent
of the affected records. Without a trustworthy surviving source, AFP cannot
reconstruct erased history or prove a clean recovery point. Incomplete search,
mail outages, and unavailable registries can delay completion. Time pressure
does not waive approval or justify unsupported status.

## Hardening order and design cost

Textual boundaries, approval binding, provenance, correction states, and safe
fallbacks come first. Among the four previously proposed extensions:

| Priority | Extension | Benefit | Cost and limitations |
|---|---|---|---|
| 1 | Optional JSON summary, now specified | Reduces field omission and parsing ambiguity | Low to medium; human text stays canonical. Offline structure checks do not prove truth, authorization, or identity. |
| 2 | Dedicated ledger mailbox with role-specific access | Limits exposure of the owner's primary corpus | Medium operational cost. Send-only needs trusted read cooperation; labels alone are insufficient. Not deployed here. |
| 3 | Per-agent signatures | Binds covered text to a trusted key | Medium to high key-management cost. Public keys must be trusted independently of a writable registry; signatures do not prove platform identity, approval, or receipt truth. A compromised signer can sign false content. Not implemented here. |
| 4 | Per-matter hash chain | Can expose some changes or missing links relative to trusted checkpoints | Requires canonicalization, fork handling and an independently trusted anchor. A bare chain cannot guarantee detection of tail deletion, whole-chain loss or recomputation. Not implemented here. |

The optional summary is a document/data contract, not a running parser or
email automation. IDs, approved-message snapshots, and attributed observation
records provide useful near-term controls without deploying a server. No
extension changes the requirement for specific trusted owner authorization.

## Questions for adopters and auditors

1. **Where is approval checked?** At a trusted boundary binding the final
   payload. This repository cannot verify your runtime; inspect it separately.
2. **What stops instructions in receipts?** PROTOCOL.md §1 forbids their
   authority; actual resistance requires runtime enforcement, not just quoting.
3. **Can evidence upgrade?** It remains possible through noncompliance. §4
   requires observer-scoped records; a filing reader cannot inherit original
   access. Test summaries and migrations for loss of those qualifiers.
4. **Does no-delete deadlock repair?** No. §§9–10 allow approved linked
   corrections, preserve history, and explicitly hold unresolved cases.
5. **What is the minimum capability?** Independent completion needs read/search
   plus send. Modify/delete is unnecessary; split roles must attribute their
   observations and incomplete steps.

## Non-goals and unverified scope

AFP does not provide non-repudiation, truthful agents, confidentiality against
the provider, immutable storage, real-time coordination, exactly-once delivery,
authentication of approvals to third parties, or account recovery. This
revision has not tested any platform, real submission, mail connector, approval
UI, actual OAuth scope, prompt-injection success rate, cryptography, or
end-to-end delivery. Synthetic examples and local checks establish only the
document and data properties actually inspected.
