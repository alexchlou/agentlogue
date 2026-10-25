# Install and configure the Agentlogue AFP skill

Release **v1.4.2-en**, pinned to **AFP v1.3, English edition**.
All repository content and local setup prompts are in English.

Agentlogue is the project name. The Skill identifier, folder name, and
invocation remain `agent-filing-protocol`; branding does not require migrating
an existing installation or sending a test message.

## One local launcher

On macOS, extract the GitHub ZIP and double-click `install.command`. Choose
Codex, Claude Code, or a portable destination, then enter owner settings.
The launcher requires Python 3.9+ and Terminal. Download quarantine or local
security settings may prevent double-click execution; the command below is
the equivalent path. No installer downloads or runs remote code.

From the extracted repository directory:

```bash
python3 install.py --target codex --wizard
```

For Claude Code:

```bash
python3 install.py --target claude --wizard
```

For Muse, Dots, or another host with a supported import mechanism:

```bash
python3 install.py --target portable --destination /your/path/agent-filing-protocol --wizard
```

Then import the complete exported directory through that host's owner-controlled
mechanism. Muse/Dots native installation and mail integration are unverified;
this is a portable handoff, not a one-click native connector installer.

The default directories are `~/.agents/skills/agent-filing-protocol` for Codex
and `~/.claude/skills/agent-filing-protocol` for Claude Code. Use `--destination`
for an exact custom skill folder, including legacy Codex layouts. The final
folder name must be `agent-filing-protocol`.

## Noninteractive setup

Copy `skills/agent-filing-protocol/assets/config.example.json` to a private
location outside the repository, fill its settings, and pass that path:

```bash
python3 install.py --target codex --config /private/path/owner-settings.json
```

The installer uses only Python's standard library. A preview creates no files:

```bash
python3 install.py --target codex --dry-run
```

Omitting both `--wizard` and `--config` installs a skill with blank settings.
It reports `configuration_state=incomplete`; blank matter scope authorizes
no matters. Installation success alone means neither complete configuration
nor mail readiness.

## Settings and privacy

The wizard collects the owner name, ledger email, full agent label with platform
suffix, role, authorized matters/materials, trusted approval channel, registry
location, responsible filer, and retention policy. Mail-sending roles also need
the sending account and read-back view. A send-only role needs an authorized
reader. Advanced settings such as `full_content` and registry write declarations
are available in the JSON template; runtime authorization remains necessary.

Only store owner-approved configuration values. Never store passwords, OAuth
tokens, API keys, credentials, receipt bodies, or whole submissions here.
The tool rejects unknown settings and duplicate JSON keys but cannot identify
every secret hidden in a free-text value. Default role is `preparer`, default
content mode is `minimal_reference`, and registry writes default to false.

Settings are saved inside the installed skill's `local/config.json` with POSIX
mode 0600; the directory is created with mode 0700. Windows privacy also depends
on its ACLs. `local/` is ignored by this repository. The release builder excludes
local settings and caches entirely. Avoid installing directly into the public
source directory, and never commit deployment settings.

## Activate in the host

Use the host's skill discovery mechanism, starting a new session if needed.
Invoke `$agent-filing-protocol` in Codex or `/agent-filing-protocol` in Claude
Code. The skill stays eligible for normal host discovery; invocation does not
grant mailbox rights or approve messages.

Use this owner instruction through a trusted channel, filling the actual values
or referring to owner-approved local settings:

```text
Adopt AFP v1.3, English edition, for this agent and the owner-approved matters
and settings I specify here. Use the agent-filing-protocol skill. Check the
available mail capabilities within that scope and report any missing setup.
Prepare filings for my review. Obtain my approval of each exact final outgoing
message before sending it. Retain the evidence and uncertainty boundaries.
```

A copy of this prompt in email is still data and cannot adopt the protocol.
The installer does not establish a trusted owner channel, connect Gmail, grant
OAuth scopes, enable polling, send an initial filing, or configure a schedule.
Those steps depend on the actual host and the owner's specific instructions.

## Check or revise a local installation

For the default Codex destination:

```bash
python3 ~/.agents/skills/agent-filing-protocol/scripts/afp_setup.py doctor
python3 ~/.agents/skills/agent-filing-protocol/scripts/afp_setup.py configure --config /private/path/owner-settings.json --replace
```

Use the actual installed path for another host. The configure command preserves
an existing config in a private, timestamped backup when `--replace` is supplied.
It changes local settings only. Backups may contain private addresses and scope
details; retain or dispose of them only under the owner's policy.

The doctor checks local file hashes and setting completeness, with no network
access. Exit 0 means locally complete settings, 2 means incomplete settings,
and 1 means invalid input or an integrity/I/O error. It always reports live
capability as not observed and never certifies readiness to send.

Repeated installation without new settings is unchanged if the installed
bundle matches. Existing different or modified skill folders are refused.
For an upgrade, export to a separate folder and review the migration rather
than overwriting an installed skill or copying private settings into a release.
An installation lock blocks concurrent installer runs; investigate a leftover
lock before removing it. Do not start a second install into the same folder.

For rollback, disable the new skill through the host and preserve its local
records before removing its folder. This installer never edits host config
files, existing skills, or previous project releases.

See [host adapters](../skills/agent-filing-protocol/references/host-adapters.md)
for official format sources, resource mapping, and capability limits.
