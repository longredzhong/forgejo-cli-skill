# Authentication and targeting

## Contents

- Installation and version
- Authentication without exposing credentials
- Repository selection and IDs
- Remote/branch preflight

## Installation and version

Check `command -v fj` and `fj version`. `fj` is the executable for the `forgejo-cli` package, not a Git alias. If missing, select a platform-appropriate installation method from upstream documentation and obtain approval before installing. Common options include `cargo install --locked forgejo-cli`, `brew install forgejo-cli`, and distribution packages. Do not automatically enable third-party repositories or run a downloaded installer.

```bash
fj version
fj version --verbose
fj --help
```

This skill's baseline is v0.8.0-dev. The upstream wiki includes older examples (its home page says 0.5.0), so installed help takes precedence. Do not require exactly this development version or auto-upgrade a working installation.

## Authentication without exposing credentials

```bash
fj auth list
fj -H example.org whoami
fj -H example.org auth login
fj -H example.org auth add-token
```

- `auth list` lists configured instance names; it does not validate credentials. `whoami` performs the identity check.
- OAuth login opens a browser and needs user interaction. Availability depends on the build's registered OAuth client IDs, not only server support.
- If OAuth is unavailable, the user can create a least-privilege application token at their instance's `/user/settings/applications`. Obtain it through the execution host's secure secret-input facility, not ordinary chat. Run `fj -H HOST auth add-token` with the secret delivered on stdin; omit its optional positional TOKEN argument.
- Do not read the local credential store, export its contents, or embed a token in a repository URL. An agent should neither discover nor migrate credentials by opening `keys.json`.
- In the checked source, `add-token` refuses to replace an existing host entry (which can be a successful process exit with a no-op message). Diagnose first; do not automatically log out, edit files, or revoke access. Logout removes local login information and needs authorization.
- A public read may work unauthenticated. Do not demand a token just because a public query is requested.
- Authentication and Git transport are separate. A working `whoami` does not prove Git push/SSH access.

`fj -H HOST auth use-ssh true` changes that host's default Git transport; it is not a login fix. Change it only when requested.

## Repository selection and IDs

Prefer fully qualified targets when outside a checkout or when several instances are involved:

```bash
fj repo view example.org/demo/widget
fj -H example.org repo view demo/widget
fj issue search --repo example.org/demo/widget --state all --page 1
fj pr search --repo example.org/demo/widget --state open --page 1
fj issue view 'example.org/demo/widget#42'
fj pr view 'example.org/demo/widget#43'
fj pr assign --pr 'example.org/demo/widget#43' reviewer
```

Three repository forms are accepted by the checked parser: `owner/repo`, `host/owner/repo`, and an HTTP(S) URL such as `https://host/owner/repo`. A trailing `.git` is stripped. Prefer the compact fully qualified form shown above. Browser issue/PR URLs are **not** the ID syntax: extract host, owner, repository, and number, then build `'host/owner/repo#N'`.

- A repository embedded in an issue/PR ID determines the target; `--host` is not a safe way to override an ID that already includes a host.
- `--host` alone does not necessarily retarget a command with an explicit `--remote`; avoid conflicting selectors. Use a full repository or full ID instead.
- `--repo` is command-specific. Issue/PR search and creation accept it; existing issue/PR view/edit commands use IDs. **`pr checkout` is a separate numeric-only parser**: use an inspected checkout and parent `pr -R REMOTE` selection; full issue-style IDs are rejected. Milestone/wiki/actions/release/tag groups accept a repository option. `repo view` takes its repository positionally.
- `repo labels` and `repo units` take their repository **before** the nested command, e.g. `fj repo labels example.org/demo/widget view`.
- `-R` means a Git remote for groups that expose it. `repo create` instead uses `-r/--remote` to **create** a local remote. Never generalize short flags across groups.

`FJ_FALLBACK_HOST` is a last-resort fallback, not a forced host override. In the checked source it must be a URL including the scheme, such as `https://example.org/`. Prefer explicit targets rather than changing the user's global environment.

## Remote/branch preflight

Before a branch-sensitive operation, inspect:

```bash
git status --short --branch
git remote -v
git branch -vv
fj -C /path/to/checkout repo view
fj -C /path/to/checkout pr -R upstream search --state open
```

Sanitize any credential-bearing remote URL before quoting it in a report. Never create such a URL yourself.

Automatic selection considers the available Git remotes and the current branch's upstream. With multiple remotes, select intentionally. A single remote can still be the wrong target if the user intends the parent repository of a fork.

For `pr create`, the default head comes from the local branch's tracking configuration, while the default base is the target repository's default branch. An unpushed branch or missing upstream is not solved by guessing `main`/`origin`; inspect and choose explicit `--base`/`--head` where appropriate. See the PR reference for fork and AGit behavior.
