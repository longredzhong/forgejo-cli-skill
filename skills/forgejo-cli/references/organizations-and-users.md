# Organizations, teams, and users

## Contents

- Organization discovery
- Team permissions and membership
- Organization labels and repositories
- Users and public keys

## Organization discovery

```bash
fj -H example.org org list --only-member-of --page 1
fj -H example.org org view demo
fj -H example.org org members demo --page 1
fj -H example.org org activity demo
fj -H example.org org visibility demo
```

`org visibility ORG` reads the current user's membership visibility. `--set private|public` changes it; it is distinct from the organization's own visibility. Organization visibility can be public, limited (signed-in viewers), or private (members). Do not make an organization or membership public by default.

`org create` and `org edit` support display name, description, contact information, visibility, and other settings. Inspect help before changing them. Organization edit does not expose renaming the organization's login in this baseline. Do not infer valid account names from display names.

## Team permissions and membership

```bash
fj -H example.org org team list demo
fj -H example.org org team view demo maintainers --list-permissions
fj -H example.org org team member list demo maintainers --page 1
fj -H example.org org team repo list demo maintainers --page 1
```

Teams govern organization repository access. Before a write, identify the exact organization, team, users, repository scope, and required permissions. A request to fix an access error does not authorize broad admin access.

Examples of narrowly scoped, explicitly authorized changes:

```bash
fj -H example.org org team create demo readers --description 'Read-only code access' --read-permissions code
fj -H example.org org team repo add demo readers widget
fj -H example.org org team member add demo readers contributor
```

`org team repo` takes `ORG TEAM REPO` where REPO is the repository name within the organization, not necessarily the fully qualified repository syntax used elsewhere. `member add/rm` takes `ORG TEAM USER`.

Permissions include `wiki`, `ext_wiki`, `issues`, `ext_issues`, `pulls`, `projects`, `actions`, `code`, `releases`, and `packages`. Read/write lists are comma-separated. `all`, `--admin`, `--include-all-repos`, and `--can-create-repos` broaden access and are never troubleshooting defaults. Inspect current permissions before edit, preserve unrelated settings, and read them back afterwards; do not assume an edit appends to a list.

Removing a team member/repository association changes access. Team deletion does not delete its repositories but still removes permission relationships and can prompt. Do not bypass confirmation or delete/recreate a team to alter one setting.

## Organization labels and repositories

```bash
fj -H example.org org label list demo
fj -H example.org org repo list demo --page 1
fj -H example.org org label add demo bug ff0000 --description 'Confirmed defect'
```

Organization label commands are `list/add/edit/rm` (not repository `view/create/delete`). Organization repository creation is `org repo create ORG REPO`, with repository creation options. Only create labels/repos when requested and inspect existing names to prevent duplicates.

## Users and public keys

```bash
fj -H example.org user view contributor
fj -H example.org user repos contributor --page 1
fj -H example.org user orgs contributor
fj -H example.org user activity contributor
fj -H example.org user key list
fj -H example.org user gpg list
```

Several user read commands default to the authenticated user when USER is omitted. For another person, supply their actual login. User search, repository, organization, and team listings may be paginated; inspect each command's help instead of assuming `--all` exists.

Profile edits, follows/unfollows, blocks/unblocks, email changes, and public-key uploads/removal are account mutations. Require the corresponding request. Never upload a private key. `user key upload` may guess a file if none is provided; use an explicit verified **public** key path. Do not use its `--force` option to skip private-key detection.

GPG upload/verification requires local `gpg` and the appropriate installed key. Uploading defaults to ownership verification. Do not add `--no-verify` as a convenience workaround. Removing a GPG key can unverify past commits and may require confirmation; inspect its ID/fingerprint and obtain explicit removal authorization first.
