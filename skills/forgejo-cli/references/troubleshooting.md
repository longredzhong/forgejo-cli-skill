# Troubleshooting and verification

## Contents

- Wrong or missing target
- Version/flag mismatches
- Authentication and authorization
- Blocking interactive input
- Output, CI, and retries

## Wrong or missing target

For “no repo info specified”, “can't figure out what repo to access”, or a PR that cannot be guessed:

1. Inspect the current working directory and Git remotes, without exposing credentials in remote URLs.
2. Use `-C /path/to/checkout` if branch-local context is required.
3. For most reads/writes on an existing object, use `'host/owner/repo#N'` instead of guessing a local branch's PR. For `pr checkout`, use its numeric ID in an inspected checkout and select the intended remote; the full ID is not accepted.
4. For search/create, supply the supported `--repo` or positional repository and an explicit host.
5. Avoid conflicting `--host`, `--remote`, and fully qualified IDs. A full ID's host takes precedence over a separate host option in the checked source.

`--host` specifies an instance, not `owner/repo`. `-R` means Git remote, unlike GitHub CLI conventions. Do not set a fallback host globally to mask an unresolved target.

## Version/flag mismatches

```bash
fj version
fj --help
fj issue create --help
fj pr create --help
fj pr edit 43 labels --help
fj actions secrets create --help
```

These help commands inspect syntax and do not perform the operation. Compare installed help with the relevant example. Upstream development branches and the wiki can disagree with a packaged version.

Common corrections in this baseline:

| Incorrect assumption | Use instead |
| --- | --- |
| `fj --version` | `fj version` |
| `pr list` / `issue list` | `pr search` / `issue search` |
| `pr diff ID` | `pr view ID diff` |
| `pr checks ID` | `pr status ID` (limited commit-status view) |
| `--body-from-file` | `--body-file`, only on commands that advertise it |
| labels `--remove` | `--rm` |
| `pr assign ID USER` | `pr assign --pr ID USER` |
| `pr review ID --approve` | Not exposed; list/request reviews only |
| `--repo` on every command | Supported selector or fully qualified ID |
| `--json` / `--jq` / `fj api` | Not exposed as general interfaces in the baseline |

If an essential capability is unsupported, explain the gap. Only choose an alternate client, API, or browser workflow when it is available and authorized. Do not silently export authentication or scrape credential files to build an API fallback.

## Authentication and authorization

- **Missing identity / 401:** use `auth list` and `fj -H HOST whoami`. Ask for secure reauthentication if needed; do not print credential files or repeatedly retry a failed login.
- **403:** inspect role/token-scope/repository permissions. Do not grant admin, recreate a token with unlimited permissions, or change visibility without authorization.
- **404:** can mean a wrong target or hidden private resource, not necessarily absence. Verify target and identity before creating a replacement.
- **OAuth unsupported:** use the authorized stdin application-token flow; build-time OAuth client registration varies.
- **SSH host-key unknown/mismatch:** verify the expected fingerprint via a trusted channel. `ssh-keyscan` alone does not establish authenticity. Do not disable host-key validation, blindly append scanned keys, or overwrite `known_hosts`.

## Blocking interactive input

An omitted body/title/value, bare optional value flag, OAuth login, AGit configuration question, or deletion confirmation may require interaction.

- Create/comment: supply a local `--body-file` where advertised. `-` means stdin for the checked body-file reader; do not infer stdin support on unrelated flags.
- Edit body/title/comment: supply the positional replacement text. These commands do not inherit create's file option.
- `--with-msg`, release/tag `--body`, milestone `--description`, and label `--description` may open an editor when used without their optional value. Pass a full value or omit the flag intentionally.
- Issue YAML forms: inspect and satisfy their actual form format; do not bypass required templates with generic text.
- Do not set `EDITOR=true`, pipe `yes`, or add a nonexistent `--non-interactive`/`--yes` to fake completion. Stop and explain any interaction the execution host cannot safely support.

## Output, CI, and retries

`--style minimal` is a top-level option and produces plain text, not machine-readable records. Piped output is minimal by default in the checked implementation. `LC_MESSAGES=C` can select English for predictable human inspection, but does not establish a stable parse schema.

Retain stdout, stderr, and the process exit code. Avoid piping into `head`/`grep` and then reporting the last process's zero exit as fj's success. Some application-level no-ops (existing login, canceled deletion, unchanged variable) return zero with explanatory text. Some successful mutations report on stderr.

After a write:

1. Capture the returned ID/name and any error or warning, with secrets redacted.
2. Read back the object using an explicit target and verify the fields actually requested. Label names may be silently ignored; blank issue creation may omit the milestone in the checked source.
3. For merges/releases/dispatch, distinguish submitted, completed, passing, merged, draft, and published states.
4. If verification fails, report the discrepancy; do not claim success from exit status alone.

`pr status --wait` is not a CI success gate. The checked source waits for reported statuses to stop being pending and then returns success regardless of their result. It does not prove all expected checks were reported, nor that reviews/protections are satisfied. Use a bounded timeout and report unresolved/pending checks faithfully.

For 429 or transient read failures, respect Retry-After/server guidance and retry with a bounded backoff if appropriate. For ambiguous writes, inspect existing objects/runs first to avoid duplicates. Never automatically repeat delete, dispatch, publish, merge, or comment operations simply because the connection closed.
