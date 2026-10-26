# Release validation and provenance

These are development tools, not part of mailbox setup. The installed Python
helpers use the standard library and do not download or send anything. CI may
download pinned validation dependencies; it uses synthetic records and has no
Gmail credentials or live deployment settings.

## Reproduce local checks

Use Python 3.9+ in a separate development environment and install the pinned
`requirements-checks.txt`. Obtain Gitleaks 8.30.1 from its official release and
verify the archive against the published checksum before running it. Supply the
actual executable path. Do not copy credentials or an installed Skill into source.

```bash
python -m pip install -r requirements-checks.txt
python scripts/sync_skill.py --check
python scripts/validate_release.py --gitleaks /path/to/gitleaks --output ../validation-new --artifacts ../artifacts-new
```

The output/evidence directory must be new and outside source. Archive output
must also be outside source; existing archives are not overwritten. For a later
run, choose new directories. Developer dependency installation is separate from
the offline validator. [Gitleaks release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1).

For a standalone test run, use `python -I -B -m unittest discover -s tests -v`.
The `-B` flag prevents the test loader from creating bytecode in the release
tree. Generated pycache is rejected rather than silently shipped or trusted.
For structured counts use `scripts/run_tests.py --output ../counts-new.json
--log ../private-tests-new.log`. Counts distinguish methods that passed, failed,
errored, skipped, had expected failures/unexpected successes or did not run.
They are not a model-behavior denominator. See [conformance](conformance.md).

Git attributes preserve LF text bytes on all platforms and treat the PNG as
binary. Keep these attributes when cloning or exporting: automatic CRLF
conversion changes the byte-pinned protocol and invalidates the Skill manifest.
Manifest and archive entries use case-sensitive POSIX relative-path ordering,
independent of the host operating system's path comparison rules.

The validator runs the full regression suite, offline Draft 2020-12 schema
checks and negative controls, canonical-resource/manifest comparisons, version
mapping, relative Markdown paths, SVG/PNG structure and metadata checks, custom
privacy patterns and Gitleaks over all UTF-8 content including SVG. A synthetic
token must trigger the scanner control. It then builds both archives and checks
their actual member bytes against the source inventory. Archives have ordered
members and a fixed timestamp; exact repeatability is tested within the same
Python/zlib toolchain, not promised across every compression implementation.

The archives, SHA256SUMS.txt and SOURCE-MANIFEST.json are suitable for review.
Review validation evidence separately before making any part public. No local
settings, scanner fixtures, Git metadata, caches or build output enter the ZIPs.
`scripts/sync_skill.py` regenerates mapped resources and the manifest after an
intentional canonical change; `--check` verifies without modifying them.

## Evidence boundaries

The canonical GitHub repository instance is `alexchlou/agentlogue`, numeric ID
`1433716711`. Refresh the live numeric identity before future publication or
cleanup; the same URL can be recreated. A fork may have another ID and must be
identified as such. Local offline validation does not discover that ID by
network access. CI records its actual GITHUB_REPOSITORY_ID and whether it
matches this expected instance.

Reports contain UTC start/end, source kind, HEAD commit/tree, dirty state,
inventory, tool versions, check layers and exact test outcome counts. HEAD's
tree identifies the checkout base; a dirty candidate's bytes are bound by its
actual inventory, not by HEAD alone. A source export without Git records missing
provenance as null/unknown, never guessed main. Checked-out/event SHA and PR
head SHA are separate. `job_key` is the workflow identifier; a numeric API
`job_api_id` remains null unless supplied through an observed, trusted context.
Neither a platform badge nor this report establishes independent publisher trust.

Reachable local Git commit identities/messages and ref/tag metadata receive
the same candidate checks as public text and join the Gitleaks input when
available. Scanner inputs exist in a private temporary directory that is
cleaned up; redacted output is not a claim that raw input never touched disk.
A source export reports that Git
check unavailable. Unicode/JSON-escaped candidates are checked; there is no
filename-suffix exemption. These conservative heuristics can require review
and are not complete identity/credential parsers. They cannot verify retained
server objects or close a historical cleanup case. CI runs after push and
cannot guarantee data was never public. An existing local hook protects its
own clone only; this change does not install or replace hooks.

## Safe CI evidence

`--ci-export ../ci-export-new` creates an allowlisted public view after all
required local checks, and only copies archives with verified digests. It is
separate from raw local diagnostics. The two folders are validation-evidence
(closed-schema JSON and the public inventory) and candidate-archives (declared
ZIPs and checksums). Private configs, raw logs, environment dumps, scanner
controls and workspace directories are never upload targets. Failed validation
exports only a fixed stage/error summary and no candidate archives. Failure
before the validator starts can leave no validator summary at all.

The prepared workflow retains counts per matrix job and makes release-checks
depend on that matrix. Upload-artifact v7.0.2 is pinned to commit
`cf430e030ddbb5b0abf93d22962f4752f3646cd9`, resolved from its official repository.
The workflow uses retention-days 0 to inherit existing repository policy.
A 30-day CI retention proposal is not applied and does not alter an owner's
mail/Skill retention. Any later explicit duration must respect repository
limits. Workflow edits and offline checks are not observed remote execution
or proof that an artifact has actually been uploaded.

Unreleased builds retain release.json's base label and set candidate_only in
validation evidence. Their inventory/dirty state distinguishes them from the
published tag and assets. Preserve existing tags, Releases and downloaded
packages; do not relabel or overwrite them. A future version bump and public
publication are separate decisions. Download actual published assets for a
later publication check instead of substituting a local build digest.

A passing test count is not a security certificate. Record the exact source
commit/tree, tool versions, tested OS/Python versions, log and archive hashes.
The CI matrix is configuration until actual runs pass. A configured private
reporting form is not proof of response time. Image metadata checks do not
replace visual inspection. Native host discovery, Gatekeeper, Windows ACLs,
actual mail permissions, approval enforcement and legal compliance need their
own evidence. No check requires a real test email.

Update the version label in the editable SVG, export the PNG at 2400 by 2420,
and visually review both before a release. Keep the existing design and record
the renderer/tool versions; a geometry check cannot prove semantic agreement
between a vector diagram and its raster preview.

## Version history and publisher identity

The package version is in release.json and the listed package labels. AFP v1.3
English PROTOCOL.md retains its v1.3.1-en document-revision header and pinned
bytes. The initial public root commit is v1.4.2-en; older CHANGELOG entries are
maintainer-provided lineage, not publicly reproducible old Git commits. Future
commits cannot retroactively establish those missing baselines. Do not publish
private historical audit archives to fill that gap.

ZIP checksums, the manifest and GitHub's asset digest establish consistency;
they are not independent publisher authentication. Individual commits may carry
a valid GitHub verification badge; there is no project-wide signed-history
or independent publisher-trust guarantee here. Future signing/attestations need
a documented key/identity trust policy and a separately trusted fingerprint or
verification anchor. A signing key published only in the same compromised
account does not automatically resolve account-compromise risk.

Before publication, inspect the final candidate and exact packages, preserve
earlier versions and obtain owner publication authorization. After publication,
download the actual assets and compare them to the reviewed hashes. Source push,
GitHub Release publication and live Skill migration are separate operations.
Keep the owner's existing retention and integration evidence throughout a
separately authorized migration; do not send a duplicate test message.
