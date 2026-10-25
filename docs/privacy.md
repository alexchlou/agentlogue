# Privacy and deployment boundaries

Agentlogue supplies protocol documents and offline installation/configuration
helpers. These helpers make no mail, OAuth, network or telemetry calls. Mail
tools, models and providers are supplied by the selected host and have their
own data handling and permissions. This statement is not an assessment of
those providers or a legal-compliance certification.

## Local settings and records

Settings can contain the owner's name, account addresses, authorized matters,
reader labels, scope and retention choice. They are private deployment data,
not credentials or permission grants. Never put passwords, keys, OAuth tokens,
mail contents or submitted materials in configuration fields.

On POSIX systems, the helper requires an owner-owned local directory with mode
0700 and configuration files with mode 0600. It rejects unsafe existing paths
without silently changing them. Windows confidentiality also depends on ACLs;
the helper does not certify them. Complete first-time config publication needs
hard-link support on the same filesystem. Unsupported filesystems fail without
publishing a partial config. Atomic visibility is not a universal power-loss
durability guarantee. Abrupt termination can leave a private temporary file.

Explicit configuration replacement preserves a private backup. This is not
permission to delete older settings, records or temporary recovery material.
Stop conflicting configuration writers before replacing settings; arbitrary
external writes and full transactional crash recovery are not guaranteed.

## Before using real mail

Identify the purpose, relevant people and materials, permitted readers, actual
host/model/mail providers, provider scopes and approved destinations. Consider
whether other people's information has an appropriate processing basis and
whether notice, provider agreements, transfer safeguards or a formal impact
assessment apply. Owner approval alone does not establish those requirements.
Check actual provider terms and applicable jurisdictions before deployment.

Use only authorized matter-specific material, with minimal references as the
default. Shared mail credentials, broad OAuth scopes and labels do not establish
matter-level isolation. Full-content email needs specific approval and review
of third-party and sensitive content. Validate the provider's permitted use;
do not assume a mailbox is an unrestricted general-purpose backup service.

The owner selects retention and handling for the relevant mail, settings,
approval snapshots, logs and backups. A review date is not automatic deletion.
Any deletion, rights request, export, forwarding or new recipient needs its own
appropriate authority and actual provider capability. Record unresolved
retention/rights issues rather than claiming they have been implemented.

## Public releases and incident reports

Public examples use reserved synthetic email addresses and fictional events.
Releases exclude local deployment settings, private integration records and
caches. The author attribution is deliberately public. Checksums do not make
private data safe to publish.

Report suspected vulnerabilities through the private route in SECURITY.md.
Use a synthetic reproducer and redact settings, message identifiers and
unpublished materials before submitting a report. A public issue is suitable
for non-sensitive documentation or feature questions, not disclosure of secrets.
