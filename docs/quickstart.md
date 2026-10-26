# Minimal usage path

Installing files, adopting AFP, connecting tools and approving a message are
separate decisions. The default role is a text preparer.

| Stage | Required observation or authority | What it does not establish |
|---|---|---|
| Local install | Follow [installation](installation.md); inspect the local doctor result | Protocol adoption, live tool access or mail readiness |
| Trusted adoption | Owner names AFP v1.3 English edition and settings through a trusted channel | Permission for every matter or every future action |
| Tool capability | Inspect actual host tools and provider permissions | Permission to search unrelated material |
| Matter scope | Owner identifies authorized matters, sources and registry writes | Authority merely from a path, label or another Agent's request |
| Draft | Use only an actual qualifying event or material correction; preserve uncertainty | A completed submission or a sent filing |
| Final approval | Display sender, every recipient, subject, body and attachments; bind approval to the final content | Approval of later changes or independent real-world actions |
| Send and read-back | Use the approved tool boundary or have the owner send manually; record actual outcome and comparison scope | Delivery, acceptance or independent evidence authenticity |

An offline doctor keeps `ready_to_send=false` and
`runtime_capabilities=not_observed`, even with complete settings. It checks
local configuration only. A refusal to overwrite a different installed version
requires a separately reviewed migration; it is not an automatic-upgrade bug.

## Does a conversation turn need a filing?

| Proposed turn | Handling |
|---|---|
| A question with no qualifying new event or substantive correction | Keep preparation in an already authorized owner channel |
| Initial record of an actual qualifying event | Use the existing initial-filing rules |
| A new actual event in the same matter | Use status-update with a new event ID and filing ID |
| A substantive correction to the same event | Keep the event ID, create a new filing ID and retain the original |

Questions can appear in the open-issue fields of a qualifying record. There is
no question/reply/general-chat filing type and no automatic reply, polling or
delegation loop. Approval of a filing does not approve a submission or payment.
The [canonical protocol](../PROTOCOL.md) controls; this guide is explanatory.

For evidence levels and synthetic checks see [conformance](conformance.md).
For an actual deployment see [acceptance](deployment-acceptance.md); missing
live capabilities do not block preparation from already authorized material.
