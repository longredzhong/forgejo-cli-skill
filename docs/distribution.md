# Distribution, ZIP releases, and npm/npx

## Status and design

The repository ships one portable skill at `skills/forgejo-cli/`. The distribution code is implemented; no registry ownership, public npm package, GitHub release, or successful hosted workflow run is implied by local tests.

Three installation paths serve different needs:

| Path | What is published | Installer |
| --- | --- | --- |
| Git | A ref containing `skills/forgejo-cli/SKILL.md` | `npx skills add REPOSITORY --skill forgejo-cli` |
| Release ZIP | Skill-only ZIP and SHA-256 manifest | Extract into the agent's supported skills parent directory |
| npm | Versioned tarball with skill plus a small `bin` installer | `npx forgejo-cli-skill@VERSION install --dir PARENT` |

The standard skill remains usable without Node or Python once copied. The npm executable installs Markdown; it does not wrap fj, authenticate, discover agents, modify shell configuration, or contact services. There are no dependencies or install lifecycle scripts. A package download through npm/npx still requires registry access unless already cached.

## ZIP layout and reproducibility

```text
forgejo-cli-skill-0.1.0.zip
└── forgejo-cli/
    ├── SKILL.md
    └── references/
        └── *.md
```

The ZIP contains only regular allowlisted skill files, one top-level directory, sorted references, fixed ZIP timestamps, and mode 0644. It refuses symlinks, unexpected payload files, missing references, and existing build outputs. It does not package `.git`, local configuration, tests, npm code, credentials, or generated caches. Compression output is verified as reproducible with the same Python/zlib toolchain; no cross-compressor byte-identity claim is made.

`package.json` is the single version source. Stable `MAJOR.MINOR.PATCH` versions are supported in the initial release builder. Prerelease/build-suffix tags are intentionally rejected rather than silently mislabeled as stable.

Build into a fresh output directory:

```bash
python3 -I scripts/build_release.py --output dist
```

Outputs are `forgejo-cli-skill-VERSION.zip` and `SHA256SUMS`. To enforce release provenance, `--tag vVERSION` additionally requires the tag to match the package version and resolve to the checked-out HEAD commit. Local untagged builds omit that option and make no release-tag claim.

After downloading published assets into a new directory, inspect the manifest and verify it before extracting:

```bash
sha256sum --check SHA256SUMS
unzip -l forgejo-cli-skill-0.1.0.zip
```

These commands assume the release is version 0.1.0; use the actual version. Obtain both assets from the trusted release source. A checksum delivered by an attacker alongside a ZIP does not authenticate that ZIP.

## GitHub release workflow

The current repository remote is GitHub, so this project's publication workflow uses GitHub Actions and `gh`. The installed skill's Forgejo operations remain fj-based; the choice of host for this repository does not change the skill's target platform.

[release.yml](../.github/workflows/release.yml) runs only for pushed `v*` tags:

1. Check out the tagged source without persisted Git credentials.
2. Run Node installer tests, Python structure/distribution tests, and the actual offline tarball/npx smoke test.
3. Reject a version/tag/HEAD mismatch and build the deterministic ZIP plus checksum.
4. Pass artifacts from the read-only build job to a separate `contents: write` release job.
5. Verify the checksum, then create a **draft** release with both assets using `gh release create --verify-tag --draft`.

Official Actions are pinned to full commit SHAs. The release job does not execute source build scripts with its write token, implicitly create tags, clobber existing releases/assets, or publish npm. CI artifacts expire after seven days; actual release assets have their own lifecycle.

Before the first real release:

- Merge/review the distribution implementation, choose the project license, and update version/lockfile/README examples together.
- Ensure Actions is enabled and the repository permits the release job's requested permissions. Fork PR tests receive no publication credentials.
- Run the local checks, review the ZIP file list/checksum, and inspect the npm tarball.
- Create and push the intended annotated tag only when release preparation is authorized. Pushing a matching tag initiates the draft workflow.

For example, these are **maintainer operations to run deliberately**, not setup commands executed by the installer:

```bash
git tag -a v0.1.0 -m 'Release v0.1.0'
git push origin v0.1.0
```

After inspecting the draft, assets, notes, and commit, publish it from the GitHub UI or explicitly:

```bash
gh release edit v0.1.0 --draft=false
```

If a draft/release already exists, the workflow fails instead of overwriting it. Inspect the previous result before recovery; do not move the tag, delete releases, or replace assets automatically. Do not treat a created draft as a published release.

## npm research: what npx actually installs

`npx skills add REPOSITORY` downloads/runs the **Skills CLI** npm package and installs skills from Git. Merely using npx does not mean the skill itself is hosted in the npm registry. This remains the simplest ecosystem-native route for a standard skill repo.

For direct `npx forgejo-cli-skill@VERSION ...`, npm needs a package containing:

- A unique available name/version and `repository` metadata.
- `bin` mapping `forgejo-cli-skill` to an executable with a Node shebang.
- A `files` allowlist containing `bin/`, `lib/`, and the complete standard skill directory.
- An engine requirement matching the runtime (here Node 22.14+), and an explicit registry/access configuration.

This repository implements those fields in [package.json](../package.json). Its installer requires `install --dir PARENT`, supports a no-write `--dry-run`, rejects existing destinations including dangling symlinks, reserves installation directories exclusively, and verifies source files before copying. It never merges into a preexisting skill. Failed-copy cleanup removes only the files/directories it created, not an arbitrary directory tree. There is no auto-update or overwrite mode.

The Skills CLI also documents **experimental** synchronization of skills shipped in installed npm dependencies (`experimental_sync`, including `npm:` declarations in package skill arrays). That can discover `skills/<name>/SKILL.md` in this package. It is an evolving opt-in ecosystem path, not the basis of this installer and not a claim that every Skills CLI version accepts `skills add npm:PACKAGE`.

## Package inspection and local smoke tests

```bash
npm ci --ignore-scripts
npm test
python3 -I -m unittest discover -s tests -v
npm pack --dry-run --json --ignore-scripts
```

The Python test creates an **actual** npm tarball, checks its complete file allowlist, and runs `npm exec --offline --package LOCAL_TARBALL -- forgejo-cli-skill install ...` in a temporary HOME/cache/config environment. It verifies installed bytes and refusal of a second install. npm exec is the underlying mechanism used by npx. No npm registry request, fj login, or remote repository mutation is needed for this smoke test.

The package manifest intentionally has no automatic `prepare`, `preinstall`, `install`, `postinstall`, or `prepublishOnly` scripts. Publishing does not depend on hidden build-time mutation. Development commands listed in `scripts` are invoked explicitly. ZIPs and tarballs stay outside Git under ignored output paths.

## First npm publication and licensing

Package-name availability and npm account ownership have **not** been verified. Before publication, choose an available unscoped name or an organization/user scope you control, update metadata consistently, and verify it with the registry. The existing name is a proposed package name, not a reservation.

The repository has no selected open-source license. `license: UNLICENSED` accurately avoids granting a license by implication; it is **not** an open-source license. A maintainer must explicitly choose terms before public distribution and add the corresponding license file/metadata. Do not inherit upstream's dual license automatically.

The first public npm publication normally requires a maintainer-controlled npm account/session and package setup. Use npm's browser login and 2FA/secure secret mechanism; never paste credentials in a task, README, workflow, or token file tracked by Git. Inspect a local tarball first and publish that reviewed artifact only when authorized. Version names on npm cannot be reused after publication; choose a new version for corrections.

No npm login, name registration, or publish was performed during implementation. Do not advertise the versioned npx command as available until the package really exists.

## Optional manual npm OIDC workflow

[npm-publish.yml](../.github/workflows/npm-publish.yml) is manual-only and is separate from tag-triggered ZIP releases. To enable it:

1. Bootstrap the package under an npm account/organization you control and select the license.
2. In npm package settings, configure a GitHub Actions **Trusted Publisher** for the exact repository and workflow filename `npm-publish.yml`, including environment `npm` when configuring that restriction.
3. Configure the GitHub environment `npm` with required reviewer and permitted version-tag rules appropriate to the repository. An environment name by itself does not establish an approval gate.
4. Ensure the workflow exists on the default branch and on the intended release tag. Node 24 supplies a suitable modern npm; npm trusted publishing requires at least npm 11.5.1 and Node 22.14.0.
5. Dispatch the workflow at the stable version tag, **not** at main:

```bash
gh workflow run npm-publish.yml --ref v0.1.0
```

The read-only build job validates tag/version/HEAD, tests, and packs the tarball. The protected publish job downloads that tarball and publishes it with `--access public --provenance --ignore-scripts`; only this job requests `id-token: write`. It does not use `NPM_TOKEN` or rebuild from a moving branch. Dispatching at main fails tag validation. OIDC authentication, environment enforcement, and publication must be verified during the separately authorized first hosted run; local tests do not establish those external settings.

A published npm version is a separate event from a published GitHub release. The workflows do not silently link their success states or automatically retry irreversible publication.

## Research sources

- [Agent Skills specification](https://agentskills.io/specification): portable directory, required metadata, relative references, progressive disclosure.
- [Skills CLI commands](https://github.com/vercel-labs/skills/blob/main/docs/commands.md): Git/local/direct-source installation and npm dependency synchronization (experimental).
- [npm package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json): `bin`, `files`, `engines`, repository/license/publishing metadata.
- [npm exec](https://docs.npmjs.com/cli/v11/commands/npm-exec): npm/npx package execution.
- [npm publish](https://docs.npmjs.com/cli/v11/commands/npm-publish): package inclusion, dry runs, access and immutable version identity.
- [npm trusted publishers](https://docs.npmjs.com/trusted-publishers/): OIDC configuration and minimum versions.
- [npm provenance](https://docs.npmjs.com/generating-provenance-statements/): supported CI, repository metadata, and `id-token` permission.
- [GitHub CLI release create](https://cli.github.com/manual/gh_release_create): draft assets, explicit tag verification, and non-atomic publication behavior.
