# Agentlogue

**Agents talk. Work stays on record.**

Let Muse, Dots, and other personal agents keep a shared record and continue
the conversation through your mailbox, using the **Agent Filing Protocol (AFP)**.

Skill and documentation package **v1.4.3-en** | Protocol **AFP v1.3, English edition** | 2026-10-26

## Author

**Alexander C. H. Lou** is the author of Agentlogue.
The project is distributed under the [MIT License](LICENSE).

The project name is **Agentlogue**. Its protocol remains **Agent Filing
Protocol (AFP)**, and its portable Skill identifier remains
`agent-filing-protocol`. Existing invocation commands, configuration paths,
and record identifiers are unchanged.

## Install the skill

**One local setup for a shared filing workflow.** On macOS, extract this
repository and double-click `install.command`; choose your host and fill the
owner settings. Python 3.9+ is required. Or run from the extracted folder:

```bash
python3 install.py --target codex --wizard
```

Use `--target claude` for Claude Code. Muse, Dots, and other agents can receive
the portable skill through their supported import mechanism; their native
installation interfaces have not been verified. The installer configures
local files only. Authorize the mail connector in the actual host and approve
each exact outgoing message when the time comes.

- [Installation, configuration, and rollback](docs/installation.md)
- [Portable skill entrypoint](skills/agent-filing-protocol/SKILL.md)
- [Configuration template](skills/agent-filing-protocol/assets/config.example.json)
- [Host support and verification limits](skills/agent-filing-protocol/references/host-adapters.md)

Installing the skill does not adopt the protocol. Give the agent a trusted
owner instruction naming **AFP v1.3, English edition**, with the applicable
owner settings and matter scope. Missing settings are reported; offline checks
never claim that live mail capability has been observed. Invocation: Codex
`$agent-filing-protocol`; Claude Code `/agent-filing-protocol`.

## In plain language

Agentlogue is a shared work log for your personal AI assistants. When Muse, Dots,
or another agent handles a submission or application, it can leave a filing
that says who did what, which version was used, what evidence exists, what
remains uncertain, and what happens next.

The assistants can continue the conversation about the same matter. Muse
records progress; Dots reads it and asks what still needs checking; Muse
responds; another agent summarizes open points and checkpoints. Linked
filings, supplements, and updates preserve that exchange for you and the
next authorized assistant.

Available, authorized mail tools do the actual reading and sending. These
may include MCP connectors; Gmail or another owner-controlled mailbox holds
the records. You set access, approve every final outgoing message, and decide
what happens next. An agent must distinguish another party's claim from
something it has independently checked.

## How agents continue the conversation

![Agentlogue, by Alexander Chanhou Lou: Muse, Dots, and other agents read and send through the owner's mailbox, with approval before every outgoing email. Four fictional dialogue turns illustrate the exchange.](assets/agent-conversation-map.png)

[Scalable SVG](assets/agent-conversation-map.svg) |
[Editable knowledge graph and conversation sequence](docs/conversation-map.md)

Roles may switch. This is an asynchronous exchange about a specific matter:
read context, raise a question, respond, and preserve the resulting record.
Emailed content follows the existing initial-filing, status-update, or
correction-supplement rules. Preparatory discussion may remain in an already
authorized owner channel. Every actual outgoing email still needs approval
and read-back; reading a message does not authorize the next action.

Muse, Dots, and other agents are illustrative participants. The diagram does
not establish installed integrations, shared account permissions, direct
agent-to-agent tool calls, or deployed automation.

## Version and language

The protocol for this edition is [PROTOCOL.md](PROTOCOL.md), in English.
Adoption requires a trusted owner instruction identifying the version and
language edition; finding a copy in email does not install or update it.
The original mixed-language package is preserved separately. This translation
does not automatically change any existing deployment.

The protocol remains AFP v1.3. Agentlogue includes a portable skill and local
setup helpers. Version v1.4.3-en fixes the sender template and local setup,
adds reproducible release validation, and retains the current conservative
refusal to overwrite a different installed version. It introduces no new AFP
message type or mailbox enforcement mechanism. Live host discovery, platform behavior, and end-to-end mail operation
have not been verified by this edition. The optional JSON Schema,
its keys and enums are unchanged, and record identifiers are preserved.
Human-readable labels and subject wording are translated; parsers of those
parts need corresponding English mappings.

| Version label | Meaning in this package |
|---|---|
| Agentlogue v1.4.3-en | Current Skill and documentation package |
| AFP v1.3, English edition | Canonical protocol adopted by an owner |
| Documentation package v1.3.1-en in PROTOCOL.md | Retained English-document revision; protocol bytes are unchanged |

The changelog distinguishes maintainer-asserted older lineage from publicly
reproducible repository history. Hashes establish byte consistency, not publisher
identity. See [release validation and provenance](docs/releasing.md).

Repository text, examples, and diagrams are in English. In actual use, receipts
must still be quoted in their original language, with any translation separate.

## Controls and limits

1. **Data stays data.** Filings, receipts, attachments, submitted text, and
   linked content cannot grant authority or change standing instructions.
2. **Approval covers the final message.** Each message requires explicit owner
   approval of its exact sender, all recipients, subject, body, and attachments.
   Any change invalidates that approval. A filing cannot authorize submission,
   payment, outreach, or unrelated data access.
3. **Labels are claims.** A full name plus platform suffix reduces same-name
   confusion; it is not authentication or a platform endorsement.
4. **Evidence has an observer and a scope.** Record who observed the source,
   what the current recorder actually read, whether the original can be read
   again, and which claim it supports. Reading a quoted receipt in someone
   else's filing is reading a filing, not independently reading the original.
5. **History is preserved.** Corrections are new, approved records linked by
   stable IDs. They do not silently replace earlier emails.
6. **Verification has a result.** Keep the approved and actual sent versions;
   record where read-back occurred and whether it matched, differed, or was
   unavailable. A Sent copy alone does not establish the recipient's view.
7. **Uncertainty stops dependent action.** Conflicting records, unknown send
   results, or material integrity problems are reported and held for review.
8. **Access is bounded.** Define matter-level authorization, content mode, and
   retention. An email label is not assumed to be an access-control boundary.

AFP provides procedural controls. It does not promise authentic agent
identity, cryptographic evidence, an immutable mailbox, atomic duplicate
prevention, exactly-once delivery, or recovery of a compromised account.

## Adoption

The owner selects the mailbox, authorized agents and matters, trusted approval
channel, registry location, content mode, and retention policy. Use the
capability table in PROTOCOL.md §11 before enabling an agent:

- A self-contained filer needs **read/search and send**, with access to the
  relevant records and read-back location. Modify/delete is unnecessary.
- A send-only participant needs an explicitly authorized reader to perform
  pre-send search and post-send verification. It cannot claim independent
  completion of those steps.
- A read-only auditor can inspect and report, but cannot email an update.

No mail is sent merely because the protocol has been adopted. Approval of each
final message remains necessary. If the runtime cannot bind approval to the
final payload, the owner sends it manually or uses a trusted confirmation
mechanism that can do so.

## Files

For deployment data and retention boundaries, see [Privacy](docs/privacy.md).
For a private vulnerability report, see [SECURITY.md](SECURITY.md).

| File | Purpose |
|---|---|
| [skills/agent-filing-protocol/SKILL.md](skills/agent-filing-protocol/SKILL.md) | Portable agent workflow and resource routing |
| [install.py](install.py) | Offline local installer with optional setup wizard |
| [docs/installation.md](docs/installation.md) | Host setup, private settings, checks, and rollback |
| [tests/test_setup.py](tests/test_setup.py) | Isolated installer and configuration tests |
| [tests/test_hardening.py](tests/test_hardening.py) | Permission, atomic-publication and failure regression tests |
| [scripts/validate_release.py](scripts/validate_release.py) | Development-only validation and release packaging |
| [PROTOCOL.md](PROTOCOL.md) | Canonical rules and evidence model |
| [templates/filing-email.md](templates/filing-email.md) | Consistent email template |
| [templates/registry-entry.md](templates/registry-entry.md) | Local observations, conflicts, and read-back results |
| [examples/example-filing.md](examples/example-filing.md) | Entirely synthetic filing, downstream reading, and correction |
| [examples/example-summary.json](examples/example-summary.json) | Optional structured summary of the synthetic filing |
| [schemas/filing-summary.schema.json](schemas/filing-summary.schema.json) | Offline-validatable optional summary structure |
| [docs/conversation-map.md](docs/conversation-map.md) | Editable knowledge graph and illustrative conversation sequence |
| [assets/agent-conversation-map.svg](assets/agent-conversation-map.svg) | Indigo editorial vector diagram |
| [assets/agent-conversation-map.png](assets/agent-conversation-map.png) | README-compatible diagram preview |
| [SECURITY.md](SECURITY.md) | Threat model, capability limits, and hardening tradeoffs |
| [CHANGELOG.md](CHANGELOG.md) | Version history and migration notes |
| [LICENSE](LICENSE) | MIT license and retained copyright notice |

JSON is optional and remains untrusted data. Schema validity does not establish
truth, authorization, or identity. Human-readable text is canonical; conflicts
with JSON must be resolved before the record is relied on.

## License

Agentlogue is distributed under the **MIT License** (SPDX identifier: `MIT`).
The same license applies to the GitHub package and the standalone skill,
including the AFP protocol text, other documentation, diagrams, templates,
schemas, examples, and scripts supplied by this project. This release keeps
the existing license and copyright notice unchanged.

### What you may do

You may use AFP privately or commercially, modify it, share copies, sublicense
it, and sell copies. You may also include it in proprietary products. MIT does
not require you to publish your modifications or make your own product open
source.

### What you must keep

Keep the original copyright notice and MIT permission notice in all copies
or substantial portions of AFP. Carrying the complete license file with a
redistributed or modified package is a straightforward way to preserve them.
The retained copyright notice is:

```text
Copyright (c) 2026 Alexander Chanhou Lou
```

### Warranty and operational permissions

AFP is supplied without warranties, and the license limits the authors' and
copyright holders' liability as stated in its full text. This explanation is
only a summary; the [LICENSE](LICENSE) file contains the actual terms.

Copyright permission to reuse AFP does not provide Gmail or other platform
access, rights over private mailbox content, or approval to send a message.
Operational authorization and final-message approval remain governed by the
owner's instructions and the actual platform permissions. Public examples
are synthetic; private deployment settings and integration records are not
included in either release archive.

Official reference: [The MIT License, Open Source Initiative](https://opensource.org/license/mit).
