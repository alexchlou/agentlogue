# Host adapters and deployment limits

Agentlogue uses the portable `agent-filing-protocol` Skill and its SKILL.md
entrypoint. The installer copies local
files and settings; the host supplies tools and enforces permissions.

| Host | Installation or import | Invocation | Verification in this release |
|---|---|---|---|
| Codex | `python3 install.py --target codex --wizard`; default `~/.agents/skills/agent-filing-protocol` | `$agent-filing-protocol` | Installer and file layout tested in an isolated home; live discovery and mail tools not tested |
| Claude Code | `python3 install.py --target claude --wizard`; default `~/.claude/skills/agent-filing-protocol` | `/agent-filing-protocol` | Installer and file layout tested in an isolated home; native runtime not tested |
| Muse | Export with `--target portable --destination /chosen/path/agent-filing-protocol`, then use its owner's supported instruction/skill import | Host-dependent | Manual integration guidance only; no native installation API verified |
| Dots | Same portable export and owner-controlled import | Host-dependent | Manual integration guidance only; no native installation API verified |
| Other agent | Load the complete skill directory through its supported mechanism | Host-dependent | Standard-format portability, not universal runtime compatibility |

For a Codex environment that uses a legacy or custom skill root, specify the
exact folder with `--destination`; for example
`--destination ~/.codex/skills/agent-filing-protocol`. The installer does not
change `config.toml`, platform settings, a model, or existing skill policy.
If the host does not list the new skill, start a new session or use its local
skill discovery mechanism; do not assume filesystem success means discovery.
Use only one active copy per host to avoid duplicate-name ambiguity.

## Mail capability checks during authorized use

1. Discover the actual available mail tools and account context. Tool names
   vary by host; neither a provider hint nor a configured email address proves
   that an account is connected or authorized.
2. Check allowed matters, materials, and actual search/read/send/read-back
   capabilities. Restrict tool arguments and provider scope as available.
   Broader connector powers do not expand owner authorization. Labels alone
   do not establish server-side isolation.
3. Match the role in protocol section 11. An independent filer needs the whole
   process; a send-only participant needs a separately authorized reader;
   a reader can report in the owner channel; a preparer can produce a draft.
4. Bind exact-message approval at the host tool boundary. If unavailable,
   prepare for manual sending. No helper in this package sends mail.

The setup report deliberately always states `ready_to_send=false` and
`runtime_capabilities=not_observed`, even with complete settings. These are
offline-report limits, not a prohibition on later properly authorized use.
The agent must verify capability, adoption, task scope, and final approval
at that time. Do not infer approval from a JSON field or previous install.

## References within the portable bundle

The canonical protocol is copied byte for byte. Its original repository paths
map to bundled resources as follows:

| Canonical repository path | Skill resource |
|---|---|
| `PROTOCOL.md` | `references/PROTOCOL.md` |
| `SECURITY.md` | `references/SECURITY.md` |
| `templates/filing-email.md` | `assets/filing-email.md` |
| `templates/registry-entry.md` | `assets/registry-entry.md` |
| `schemas/filing-summary.schema.json` | `references/filing-summary.schema.json` |
| `examples/example-filing.md` | `references/example-filing.md` |
| `examples/example-summary.json` | `references/example-summary.json` |
| `examples/materials/submission-demo.txt` | `references/materials/submission-demo.txt` |

## Format and host documentation

Checked on 2026-10-25:

- [Agent Skills specification](https://agentskills.io/specification)
- [Codex local skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)

Directory conventions can change. These sources support format and location
choices; they do not certify this skill or any Muse/Dots integration.
