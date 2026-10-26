# ADR 0003: trusted approval at a deployment boundary

Status: proposed architecture and tests only; no sender or gateway implemented.

Bind an actual trusted owner event to the matter and final logical payload:
selected sender, exact To/Cc/Bcc sets, subject, body, attachment names/types/
lengths and bytes. Check before the real send call. Material changes invalidate
approval. An agent-written boolean, approval assertion in email or unsigned
digest does not authenticate the owner.

Compare manual owner-send with a host-provided trusted confirmation boundary.
A new service would add security, credentials, storage and operational costs;
it is outside this maintenance scope. A manual path is legitimate but must not
be labelled runtime-enforced agent automation.

Specify supported expiry/revocation and reuse handling, safe snapshot access
and retention. An unknown send outcome must not consume a fiction of certainty
or cause automatic resend. A one-use marker is not exactly-once delivery.
Provider-added MIME headers/encoding are different from approved logical
content. Do not normalize away substantive recipient, body or attachment
changes. Missing Bcc/attachment read-back is an explicit comparison limit.

Future trusted-boundary tests must reject forged/self-issued approval and
changed or replayed payloads, and preserve uncertain outcomes. T05 exercises
only a synthetic comparison rule; it does not establish a trusted channel.
Subsequent read-back is observation, not prevention of an earlier disclosure.
