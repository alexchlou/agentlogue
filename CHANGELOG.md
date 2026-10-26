# Changelog

## Unreleased

- Use **Alexander C. H. Lou** as the owner's selected current author and
  copyright attribution across documentation, metadata, the portable Skill
  and diagrams. Keep the MIT permission/warranty text, AFP v1.3, Schema and
  Skill identifier unchanged. Earlier entries and published releases retain
  the attribution used at publication.
- Add structured test outcomes, source/CI provenance and candidate-only evidence.
  Distinguish skipped tests, missing Git provenance and PR head/checkout identity.
- Prepare allowlisted CI evidence and validated candidate archive uploads using
  a verified Action commit; inherit existing repository retention by default.
  Remote execution and actual uploads require their own observed results.
- Check reachable Git metadata and Unicode/JSON-escaped email candidates without
  publishing raw values. These checks do not establish historical erasure.
- Add 26 layered acceptance plans and 12 paired synthetic trace controls. These
  test an offline checker, not a real Agent, trusted sender or native integration.
- Consolidate usage guidance and document deferred evidence/hold/approval designs
  and deployment acceptance. Do not introduce a mail service or migrate installs.

## v1.4.3-en - 2026-10-26

- Preserve LF text bytes on Git checkouts, including Windows, so automatic
  newline conversion cannot invalidate the pinned protocol and Skill manifest.
- Order manifest and archive paths consistently across operating systems.
- Correct From to the selected sending account in both templates and worked
  examples. The ledger remains the destination; final-message approval remains
  required. Regenerate canonical resource copies and the Skill manifest.
- Tolerate documented OS metadata in package integrity checks, retain symlink
  and pycache rejection, and identify changed/unexpected/missing files.
- Support bounded UTF-8 stdin configuration, perform prerequisites before
  prompting, and retry invalid wizard fields without losing earlier answers.
- Publish complete first-time settings without overwriting a concurrent creator;
  preserve complete replacement backups; reject unsafe existing POSIX settings
  permissions/ownership; check the minimum Python version before setup.
- Add public manifest generation, isolated fault-injection tests, release
  validation/packaging and CI configuration. Add privacy/provenance explanations
  and a private vulnerability-reporting route. Actual CI execution and native
  host operation must be reported separately from local checks.
- Keep automatic in-place upgrade out of this maintenance release. Different
  installed versions remain refused pending a separately reviewed migration.
- Update package-version labels and the diagram's label in the existing visual
  design. Preserve AFP v1.3 English PROTOCOL.md, schemas, MIT notices and the
  Skill identifier. SECURITY.md gains reporting guidance; templates and setup
  helpers intentionally change. Previous version artifacts remain separate.

Older entries below describe the maintainer's retained source lineage. This
repository's public history starts at v1.4.2-en; the older byte-preservation
statements cannot be independently reconstructed from that initial root commit.
Future commits do not retroactively fill those missing public baselines.

## v1.4.2-en - 2026-10-25

- Adopt **Agentlogue** as the project name and **Agents talk. Work stays on
  record.** as its tagline. Explicitly name **Alexander Chanhou Lou** as author
  in the English README, editable conversation map, and portable Skill metadata.
- Update the SVG/PNG knowledge graph and Mermaid sources while preserving the
  Muse/Dots/other-agent dialogue and the indigo, porcelain, and gold design.
- Update the portable Skill display name to Agentlogue (AFP). Keep the Skill
  identifier, folder, invocation, protocol, configuration schema and record IDs.
- Retain AFP v1.3 English edition, both MIT LICENSE files, setup scripts,
  templates, schemas, and synthetic examples byte for byte.
- Build separate GitHub and standalone Skill packages from clean source.
  Preserve prior releases; do not update a local installation, change private
  configuration or integration evidence, or send a test message.

## v1.4.1-en - 2026-10-25

- Retain MIT for the GitHub package and standalone skill; preserve the full
  license and existing copyright notice byte for byte.
- Expand the English README with permitted reuse, notice-preservation duties,
  warranty/liability terms, and the distinction between copyright licensing
  and operational authorization.
- Bundle the same explanatory notes with the standalone skill and link them
  from its entrypoint. Update package metadata and installation-guide version.
- Keep AFP v1.3, installer behavior, schemas, templates, examples, and the
  Muse/Dots conversation map unchanged. Preserve all previous release packages.
- Exclude private deployment settings and integration records. This packaging
  update does not install or update a live skill or publish a GitHub release.


## v1.4.0-en - 2026-10-25

- Package AFP v1.3 English edition as a self-contained Agent Skills directory,
  with Codex UI metadata and portable Muse/Dots integration guidance.
- Add offline Python installation, a macOS launcher, private owner settings,
  local completeness/integrity checks, and configuration backups.
- Preserve per-message approval, original evidence, unknown-result handling,
  matter scope, and role boundaries. No mail-sending code or OAuth setup added.
- Keep the protocol, original JSON Schema, templates, synthetic examples,
  license, and conversation diagram unchanged from v1.3.1-en.
- Retain previous releases separately. Native host loading, live connector
  behavior, and end-to-end mail operations remain unverified in this release.


## Documentation package v1.3.1-en — 2026-10-25

- Produced a complete English edition of the README, protocol, templates,
  worked examples, structured-summary text, security references, and diagrams.
- Preserved the indigo-and-porcelain design and the two-way conversation
  among Muse, Dots, and other personal agents.
- Retained protocol version AFP v1.3, all JSON Schema field names and enums,
  existing identifiers, and the separation of claims, observations, and authority.
- Kept LICENSE, the JSON Schema, and synthetic submission text byte-identical.
- The original package remains separate. This is a language edition, not
  automatic adoption or deployment; explicitly identify English when adopting it.

## Documentation package v1.3.1 — 2026-10-25

- Integrated plain-language Chinese and English introductions into README.
- Added Muse, Dots, and other personal agents in a two-way, matter-linked
  email conversation, with questions, responses, supplements, and updates.
- Added an indigo-and-porcelain editorial SVG, a PNG preview, and editable
  Mermaid knowledge-graph and sequence-diagram sources.
- Kept owner approval, actual connector capabilities, evidence attribution,
  read-back, and the source-data/authority distinction explicit.
- Canonical protocol, templates, Schema, security model, synthetic filing
  examples, and license remain byte-for-byte identical to package v1.3.

Package v1.3.1 is a presentation update. Its protocol remains AFP v1.3; it adds
no mail type, runtime, integration, or deployment.

## v1.3 — 2026-10-25

Security-audit document revision; no runtime or mailbox configuration deployed.

- Added explicit untrusted-data boundaries covering receipts, filings,
  attachments, links, approval claims, memory, and registry actions.
- Bound per-message approval to the complete final envelope, body, and
  attachments, with reapproval on change and a manual/trusted fallback.
- Replaced the inconsistent single four-level evidence field with observer,
  actual material, rereadability, association, and claim-scope fields.
- Added matter/event/filing IDs, timestamp provenance, concurrency limitations,
  unknown-send holds, conflict resolution, and compromise-response limits.
- Distinguished send results, read-back observations, registry synchronization,
  delivery, and acceptance. Preserved approved and actual message versions.
- Defined linked corrections and updates without rewriting history or
  requiring deletion rights; added a registry observation template.
- Added matter-level access, minimal-reference/full-content modes, retention
  choices, and an explicit read/search/send capability table.
- Generalized private operational history and replaced examples with synthetic
  material. Removed private audit handoff from the public package. Retained
  the existing license and copyright notice verbatim.
- Fixed subject consistency across canonical rules, template and examples.
- Specified an optional JSON summary and local Schema; neither proves truth,
  identity or approval. Recorded limits of signing and hash-chaining proposals.

### Migration from v1.2

Do not resend or edit old emails. Keep original wording as a historical claim
and add the current reader's actual observations to an authorized index.
Associate legacy records with IDs only after checking available sources; mark
unresolved mappings. New protocol text applies only when adopted by the owner
through a trusted channel. A copy found in a filing is not an update command.

## v1.2 — 2026-10-25

- Required platform suffixes to distinguish same-name agents.
- Documented an owner-approved supplement after an incomplete filing.

## v1.1 — 2026-10-25

- Separated status from evidence and introduced the former four-level wording.
- Added actual submitter, filing type, source URL and version fields.
- Added duplicate searches, pending registry synchronization and read-back.
- Corrected platform attribution in the reference deployment.

## v1.0 — 2026-10-25

- Initial protocol: post-submission records, verbatim receipts, per-email owner
  approval, and no silent editing or resending of another agent's filing.

Earlier entries retain substantive version history while omitting private
operational attribution and timelines. The original v1.2 audit archive is
preserved separately; this changelog does not claim that earlier public Git
history or external copies have been erased.
