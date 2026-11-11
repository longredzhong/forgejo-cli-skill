# forgejo-cli-skill

**English** | [简体中文](README.zh-CN.md)

A standard [Agent Skill](https://agentskills.io/specification) that helps coding agents use [`fj` (forgejo-cli)](https://codeberg.org/forgejo-contrib/forgejo-cli) correctly and safely for Forgejo and Codeberg. This is an independent skill project, not the upstream CLI or a credential manager.

**Distribution status:** ZIP building and the npm installer are implemented in source. No npm package or release is claimed to have been published. Git installation requires a ref containing this skill; default-branch examples apply after merge.

## Install

Install upstream `forgejo-cli` separately and check `fj version`. See the [upstream installation guide](https://codeberg.org/forgejo-contrib/forgejo-cli/wiki/Installation). The skill installer does not install fj, authenticate, or run remote operations.

### From Git with the Skills CLI

```bash
npx skills add https://github.com/longredzhong/forgejo-cli-skill --skill forgejo-cli
```

The Skills CLI discovers `skills/forgejo-cli/SKILL.md` and lets you select an agent and installation scope. This route uses the npm-hosted **Skills CLI**, but does **not** require this project to be published on npm. Inspect/pin the installer and source version when reproducibility matters.

### From a release ZIP

After a release is published, download `forgejo-cli-skill-VERSION.zip` and `SHA256SUMS` from its assets. Verify the checksum in a fresh download directory, then extract into your agent's skills directory. The ZIP has one top-level `forgejo-cli/` directory containing `SKILL.md` and `references/`; it does not contain a second `skills/` wrapper, repository tests, or credentials. Checksums detect corruption, not the authenticity of an untrusted release source.

### From npm via npx (after npm publication)

Requires Node.js **22.14+**. Once version `0.1.0` has actually been published:

```bash
npx forgejo-cli-skill@0.1.0 install --dir .agents/skills --dry-run
npx forgejo-cli-skill@0.1.0 install --dir .agents/skills
```

`--dir` is the **parent skills directory**; installation creates `forgejo-cli/` inside it. Select the directory supported by your agent. For a supported user-wide location, use `--dir ~/.agents/skills` (shell expansion), or the agent-specific parent directory. Existing files, directories, and symlinks at the destination are refused; there is no overwrite/force mode. For upgrades, review and back up the old skill yourself before installing into an absent destination.

You can test the implementation locally now, without npm publication:

```bash
node bin/forgejo-cli-skill.mjs install --dir /tmp/my-agent-skills --dry-run
```

Manual installation also works: copy the entire `skills/forgejo-cli/` directory, not just `SKILL.md`. Keep the final directory name `forgejo-cli`.

## Use

Ask your agent to perform a specific Forgejo task, for example:

- “Find timeout-related issues in this Codeberg repository, including closed issues.”
- “Read this Forgejo PR's diff, comments, and CI status without posting anything.”
- “Create an issue using the required repository template and the prepared body file.”
- “Create a PR for this branch with the specified base/head; do not merge it.”

The skill instructions are in English for portability. The entrypoint provides procedures and gotchas; references load only as needed. Writes still require the user's authorization.

## Coverage and safety

| File | Scope |
| --- | --- |
| [SKILL.md](skills/forgejo-cli/SKILL.md) | Workflow, explicit targets, noninteractive defaults, safety |
| [Authentication and targeting](skills/forgejo-cli/references/auth-and-targeting.md) | Hosts, login, remotes, repository and object IDs |
| [Issues](skills/forgejo-cli/references/issues.md) | Templates, bodies, labels, milestones, dependencies |
| [Pull requests](skills/forgejo-cli/references/pull-requests.md) | Fork/AGit, reviews, checkout, CI, merge |
| [Repositories and wiki](skills/forgejo-cli/references/repositories.md) | Creation, migration, units, labels, wiki |
| [Actions and releases](skills/forgejo-cli/references/actions-and-releases.md) | Variables/secrets, dispatch, milestones, tags, releases, assets |
| [Organizations and users](skills/forgejo-cli/references/organizations-and-users.md) | Teams, permissions, profiles, public keys |
| [Troubleshooting](skills/forgejo-cli/references/troubleshooting.md) | Flag/version differences, interactive input, output, retries |

The skill does not read `keys.json`, invent general `fj api`/JSON interfaces, treat zero exit from `pr status --wait` as passing CI, or bypass protections. The npm installer only copies bundled Markdown; it has no third-party runtime dependencies, install lifecycle hooks, network calls, or agent auto-detection. **Node is needed only for npm installation; using the installed skill does not need Node or Python.**

Examples were checked against `fj v0.8.0-dev`, not every historical or future version. Installed command help takes precedence. See [sources and maintenance](https://github.com/longredzhong/forgejo-cli-skill/blob/main/docs/sources.md).

## Development and validation

Requires Python **3.9+** for repository/ZIP checks and Node.js **22.14+** with npm for installer/package checks. Optional fj help checks do not call remote APIs.

```bash
npm ci --ignore-scripts
npm test
python3 -I -m unittest discover -s tests -v
FJ_SKILL_CLI_CHECK=1 python3 -I -m unittest discover -s tests -v
```

The Python suite checks skill structure, links, evaluation-scenario structure, reproducible ZIP contents/checksums, and an offline npm tarball/npx installation smoke test. The opt-in fj suite appends `--help` to examples in an isolated HOME/XDG directory; it does not execute their writes. The Node suite exercises installation, dry runs, collisions, invalid arguments, and symlink/payload safeguards.

For full standard-format validation, use the official validator when installed:

```bash
skills-ref validate skills/forgejo-cli
```

The [13 behavior scenarios](https://github.com/longredzhong/forgejo-cli-skill/blob/main/evals/scenarios.json) require a controlled agent evaluation environment. Structure/help tests do not establish actual agent behavior or service-side compatibility.

## Build and publish

```bash
python3 -I scripts/build_release.py --output dist
npm pack --ignore-scripts --pack-destination dist
```

The ZIP builder refuses existing outputs; use a fresh directory for a repeated build. Package version comes from `package.json`. A pushed stable `vVERSION` tag matching that version triggers a tested ZIP build and draft GitHub Release with ZIP/checksum assets. It never creates a missing tag, overwrites release assets, or publishes to npm automatically.

See [distribution and release operations](https://github.com/longredzhong/forgejo-cli-skill/blob/main/docs/distribution.md) for draft promotion, exact-tag validation, npm research, first-publication prerequisites, and the optional manual OIDC publishing workflow. The npm package currently declares `UNLICENSED`: a maintainer must make an explicit license decision and verify package-name ownership before public distribution. No upstream license is implicitly applied to this project.
