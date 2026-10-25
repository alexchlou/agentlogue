# Registry Observation Template

AFP v1.3, English edition. The registry is an index and observation history,
not independent proof of submission. Registry writes require authorization
separate from mail access. Preserve earlier observations; a current-view field
may point to the latest justified observation without erasing history.

```text
matter_id:
event_id:
filing_id:
Mail locator / Message-ID, if available: <Locates a record; does not authenticate identity>
Subject and filing date:
Related filing_id(s):
Current recorder and observation time:
Materials actually read:
Original observer and attributed source claim:
Original rereadability and basis:
Current status claim, support, and limits:
Controlled reference to approved snapshot: <Not an approval assertion inside email>
Controlled reference to actual sent version:
Approval reference and trusted channel: <No authority over unrelated matters>
send_state: not_sent / result_unknown / sent
readback_state: not_performed / match / mismatch / unavailable
Read-back location, observer, time, and comparison scope:
Differences, attachment-check scope, and impact:
record_state: active / conflict_hold / integrity_hold / corrected / duplicate
Registry sync status: pending / synced / inaccessible
Competing claims and sources:
Owner's next-step decision, grounds, and date:
Grounds for lifting holds: <Remain on hold without grounds>
Original record location, related corrections, and updates:
Content scope, access restrictions, and retention:
```

`active` means no known hold in this index, not independent verification or
acceptance. `corrected` means corrective information is linked, not history
rewritten. Multiple holds may coexist. `duplicate` describes multiple records
of an identified event, not repeated submissions. `match` describes the named
message comparison, not evidence authenticity. Never assume a match when
read-back is unavailable.

For unresolved conflict, preserve competing claims and pause dependent action.
Neither the mailbox nor a later timestamp automatically overrides other evidence.
