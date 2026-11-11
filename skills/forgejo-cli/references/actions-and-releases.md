# Actions, milestones, tags, and releases

## Contents

- Actions tasks and dispatch
- Variables and secrets
- Milestones
- Tags and releases
- Release assets

## Actions tasks and dispatch

```bash
fj actions tasks --repo example.org/demo/widget --page 1
fj actions dispatch publish.yaml main --repo example.org/demo/widget --inputs version=1.2.0
```

Tasks are paginated (up to 20 per page in this baseline). Do not assume a list contains every run. The checked Actions group exposes tasks, variables, secrets, and dispatch; it does not expose a full `gh run`-style log/cancel/watch interface.

Dispatch is a write that can deploy, publish, or consume resources. Before an authorized dispatch, inspect the actual workflow at the chosen ref for its name/filename, `workflow_dispatch` inputs, defaults, and side effects. `--inputs KEY=VALUE` is repeatable; quote the whole pair for values with spaces. Do not invent input keys or dispatch at a different ref to work around a failure.

The dispatch success message is not completion of the workflow. Inspect subsequent tasks/statuses and report if no unique run can be correlated. After a timeout, inspect recent runs before retrying.

## Variables and secrets

```bash
fj actions variables list --repo example.org/demo/widget
fj actions variables create DEPLOY_ENV staging --repo example.org/demo/widget
fj actions secrets list --repo example.org/demo/widget
```

Variable values may be exposed in listing output. Treat them as potentially sensitive, even if they are not designated secrets, and do not reproduce them unnecessarily. Omitting a variable's value opens an editor. `variables create --force` overwrites existing data; inspect and authorize first.

**Secret creation is constrained in this baseline:** `actions secrets create NAME DATA` takes the value positionally. There is no documented stdin/file-value option. Never invent `--body-file`, `--value-file`, or stdin support; environment-variable expansion still places the value in process arguments. Prefer the instance's trusted secret-entry UI or another explicitly authorized secure mechanism. Do not use the local `fj` credential store as an Actions secret source, or pass a real secret in an ordinary tool-call transcript. Secret listings expose names/metadata, not retrievable values. Do not promise to read a secret back or include it in verification output.

Variable and secret deletion are writes. Establish the exact name and target repository before deleting; never delete/recreate a secret merely to test access.

## Milestones

```bash
fj milestone search --repo example.org/demo/widget --state all
fj milestone create 'v1.2' --repo example.org/demo/widget --state open --description 'Timeout fixes'
fj milestone view 'v1.2' --repo example.org/demo/widget
fj milestone edit 'v1.2' --repo example.org/demo/widget --state closed
```

Creation requires `--state open|closed`. Give `--description TEXT` when wanted; a bare `--description` opens an editor, while omitting the option leaves it unset in the checked source. View/delete can resolve title or ID; use an unambiguous discovered value. Deletion is separate from closing a milestone. Verify requested issue/PR membership after assigning milestones.

## Tags and releases

```bash
fj tag list --repo example.org/demo/widget --page 1
fj tag view v1.2.0 --repo example.org/demo/widget
fj tag create v1.2.0 --repo example.org/demo/widget --branch main --body 'Version 1.2.0'
fj release list --repo example.org/demo/widget --include-prerelease --include-draft
fj release create 'Version 1.2.0' --repo example.org/demo/widget --tag v1.2.0 --body-file release.md --draft
fj release view 'Version 1.2.0' --repo example.org/demo/widget
fj release view v1.2.0 --repo example.org/demo/widget --by-tag
```

Before a tag/release write, verify the exact revision/branch, tag existence, release name, visibility, and draft/prerelease intent. Creation/publishing can trigger workflows. Samples are alternatives, not an instruction to create both a tag and a release.

Release creation requires either an existing `--tag TAG` or `--create-tag [TAG]`, not both. With `--create-tag` but no value, the new tag defaults to the release's name; provide an explicit tag to avoid surprises. `--branch` controls the new tag target. Tag creation through fj is remote; it does not mean a local tag was created or fetched.

`--body-file` is available on release **create**, not release edit in this baseline. Release/tag `--body` without a value invokes an editor; omission leaves the body unset. A release name and a tag are different selectors. `release view/delete --by-tag` opts into tag lookup; do not assume asset commands accept tag names as release identifiers.

A draft is not a published release. Publishing requires the corresponding explicit edit, e.g. `release edit NAME --draft false`, and user authorization. Read back the result. Do not assume deleting a release also deletes its tag, or vice versa. Tag deletion can disrupt consumers and is not a cleanup default.

## Release assets

```bash
fj release asset create 'Version 1.2.0' ./dist/widget.tar.gz widget-linux.tar.gz --repo example.org/demo/widget
fj release asset download 'Version 1.2.0' widget-linux.tar.gz --repo example.org/demo/widget --output ./downloads/widget-linux.tar.gz
```

Read the release first and inspect the local file before uploading. Prepare a new download directory and a nonexisting output filename: the checked implementation uses create-new semantics and refuses an existing output file. Do not delete an existing file to work around that error without authorization. Keep untrusted downloads separate and do not execute their contents. Asset upload or download success does not verify integrity; compare an independently trusted checksum/signature when the task requires it. Asset deletion uses the discovered release and asset name and requires authorization.
