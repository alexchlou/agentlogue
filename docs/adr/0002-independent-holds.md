# ADR 0002: independent hold dimensions

Status: proposed; no existing Registry or Schema changes.

The Registry displays one record_state line while explicitly permitting multiple
holds. This is a representation ambiguity; no state-overwrite runtime failure
has been established here.

A future sidecar could separate lifecycle, conflict holds, integrity holds,
send, read-back and synchronization. It would add parser and reconciliation
costs, so retaining text with explicit coexistence is also an option. A linked
correction must not silently clear another hold. Lifting a hold needs grounds,
time and scope; it cannot change the original observer's evidence.

T17's synthetic observations retain conflict and integrity holds simultaneously.
That trace representation is not a new AFP enum or an authorization to migrate
records. Preserve original state wording and history. Any future implementation
needs explicit versioning, compatibility fixtures and a separately reviewed
migration; the diagram of a state machine is not an operational control.
