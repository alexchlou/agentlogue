# Deployment acceptance plan

Status: design and test plan only. No production sender, approval gateway or
cross-host integration is implemented by these documents.

| Layer | Evidence needed before claiming the capability | Current public maintenance scope |
|---|---|---|
| Offline package | Bound inventory, helper tests, Schema and manifest results | Local validation reported per run |
| Native discovery | Exact host/version discovers the intended Skill and path | Not run by this maintenance work |
| Tools and scope | Actual provider scopes and available tools, tested under matter restrictions | Not verified here |
| Approval | Trusted owner event bound to the final logical envelope, body and attachment bytes | Design only; manual owner-send is a valid fallback |
| Approved send | One specifically approved final payload, actual tool result and unknown-result handling | Not run; no test email |
| Read-back | Named view, observer, time, full checked fields and unavailable parts | Not run |
| Cross-host | Each host's independent observations, correction links and reconciliation | Not run; platform names do not prove connection |

Record Codex, Claude Code, Muse, Dots and any other host separately. A supported
directory convention or an OS/Python CI job is not native-host evidence. A
send-only participant needs an authorized reader; the same connector reading
its own Sent view is not independent authentication or the recipient's view.

Before a real deployment, record roles (owner/operator/reader/provider), data
flow, actual scopes, approved destinations, permitted third-party material and
matter boundaries. Labels and a dedicated mailbox do not by themselves isolate
different matters on the server. Default to minimal references; do not copy real
submission text merely to populate a test. Record retention, backups and a
separately authorized disposal decision. Do not infer indefinite retention or
automatic deletion. An owner's approval is not a legal-compliance finding.

Unknown or unavailable observations stay explicit. Missing live access does not
block unrelated offline documentation or tests. Do not upgrade local state to
`ready_to_send=true`, invent received messages, resend historical tests, or
relax per-message approval to make an acceptance table appear complete.

See the [approval design](adr/0003-approval-boundary.md),
[privacy boundaries](privacy.md) and [usage path](quickstart.md).
