# Sources and maintenance

## Scope

This repository authors instructions for upstream `fj`; it does not vendor its source, execute downloaded upstream code, or define a new CLI. Examples use reserved example domains and illustrative names only. No license is inferred from upstream for this independently authored repository; choose a project license explicitly before distribution that requires one.

## Primary references

| Source | Used for |
| --- | --- |
| [Agent Skills specification](https://agentskills.io/specification) | Directory layout, required frontmatter, naming, relative references, progressive disclosure, validation |
| [Official specification source](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx) | Readable source of the normative format |
| [Skill authoring best practices](https://agentskills.io/skill-creation/best-practices) | Compact entrypoint, task-specific references, gotchas, execution-based testing |
| [forgejo-cli repository](https://codeberg.org/forgejo-contrib/forgejo-cli) | Authoritative CLI definitions and behavior |
| [forgejo-cli README](https://codeberg.org/forgejo-contrib/forgejo-cli/src/branch/main/README.md) | Purpose, installation entrypoints, Git/Forgejo separation |
| [forgejo-cli wiki](https://codeberg.org/forgejo-contrib/forgejo-cli/wiki) | User workflows and installation/authentication background |
| Installed `fj version` and individual `--help` outputs | Local syntax verification against v0.8.0-dev (flake build) |

Upstream `main` revision observed during research: `5a450bff924f25912f620cdcdb66cc2e984f83dd`. The source archive was downloaded from `main`; the revision is a provenance pointer, not a claim that a moving branch archive or local binary is reproducibly tied to that commit. Re-check a pinned revision when updating. The wiki's Home page declares 0.5.0 while some pages discuss later versions; do not treat it as a synchronized command reference.

## Source cross-checks

Paths below are relative to the upstream repository. Use the [observed source revision](https://codeberg.org/forgejo-contrib/forgejo-cli/src/commit/5a450bff924f25912f620cdcdb66cc2e984f83dd/src) when reproducing a check, and inspect current installed help before relying on it.

| Source path / symbol | Verified fact captured by the skill |
| --- | --- |
| `src/main.rs`: `App`, `Command`, `read_file_or_stdin` | Global host/cwd/style options; version is a subcommand; body-file `-` reader |
| `src/repo.rs`: `RepoInfo::get_current`, `RepoArg::from_str`, `fallback_host` | Full repository selection, Git remote context, fallback URL, precedence cautions |
| `src/auth.rs`: `AuthCommand::run` | OAuth vs stdin token login; existing host entry is not replaced |
| `src/issues.rs`: `IssueCommand::repo`, `create_issue`, `label_names_to_ids` | Full IDs; blank-issue/template rules; blank creation omits milestone; missing labels can be ignored |
| `src/issues/template.rs`: `get_template_file`, `generate_from_template` | Template stem extension lookup; YAML form parsing vs free-text Markdown |
| `src/prs.rs`: command definitions, `PrNumber::from_str`, `checkout_pr`, `create_pr`, `view_pr_status` | `--body-file`, positional/flag ID differences, checkout's numeric-only parser and existing-branch movement, fork base prefix, AGit side effects, non-gating CI exit |
| `src/prs.rs`: `ReviewCommand` | Reviews can be listed/requested; no approval submission command in baseline |
| `src/milestones.rs`: `create_milestone` | Required state; a bare description option, not omission, invokes editor |
| `src/actions.rs`: secret/variable/dispatch definitions | Positional secret data; repeatable input pairs; variable overwrite semantics |
| `src/release.rs`, `src/tag.rs` | Explicit tag creation/selection, create-only release body-file, draft/asset handling |
| `src/org.rs`, `src/org/team.rs`, `src/user.rs` | Organization/team selectors and privileges; public-key safety and account operations |
| `src/localization.rs` | Localized text output, `LC_MESSAGES`/`LANG` language selection |

## Initial validation record

- Official `skills-ref validate` passed. The transient validator build resolved the official Agent Skills repository to revision `83021e2be457a9b6679148719c1f6074f0ad975e`.
- All 8 repository tests passed with CLI checking enabled, including 135 distinct documented `fj ... --help` invocations against the installed v0.8.0-dev binary. Commands were parsed in a temporary HOME/XDG environment; no remote operation was executed.
- The help regression exposed checkout's numeric-only ID parser; the example and targeting guidance were corrected. Source review also confirmed that asset downloads refuse existing output files.
- The 13 evaluation scenarios have been schema/structure-checked only. No live agent behavior evaluation, remote integration test, publish, merge, dispatch, or deletion was performed.

These are initial results, not an automatically updated CI status or a compatibility promise for other builds.

## Deliberate design choices

- **One standard skill under `skills/forgejo-cli/`:** directory name matches frontmatter; only standard frontmatter fields are used. `compatibility` describes runtime requirements, while the string-valued `metadata` map records the skill version, repository, upstream project, and tested fj version. Tests enforce that the skill version matches `package.json`; this metadata travels unchanged through ZIP/npm installation. No agent-specific plugin manifests or unrestricted tool allowlists are needed.
- **No exhaustive CLI dump:** the entrypoint teaches safe procedures and routes to focused references. Installed help remains the per-command flag authority.
- **No wrapper or credential reader:** run `fj` directly. A wrapper would add quoting/compatibility failure modes and unnecessary secret access.
- **No universal API/JSON fallback:** the baseline does not offer those interfaces. Unsupported operations remain explicit limitations instead of prompting credential extraction.
- **Testing in layers:** static project checks, opt-in offline CLI help checks, and human/agent behavioral scenarios. Actual mutation and remote integration tests require a separately authorized disposable repository.

## Updating

1. Record `fj version --verbose`, upstream revision, and relevant wiki version notes.
2. Re-read changed command definitions **and execution paths**, especially targeting, editor triggers, templates, authorization, and status handling.
3. Update only the affected reference and the entrypoint gotchas as needed.
4. Run the static tests and the opt-in CLI help suite. If help differs, establish whether a capability is new, removed, or merely renamed before editing.
5. Run selected evaluation scenarios in an isolated environment. For live integration tests, require an explicitly authorized disposable instance/repository and verify every write by readback.
6. Do not claim runtime/agent behavior was tested if only help parsing or scenario linting ran. Do not copy credentials, personal configuration, prompt-injection text, or whole upstream documents into this repository.
