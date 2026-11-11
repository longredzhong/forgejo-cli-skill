# Issues

## Contents

- Inspect and search
- Create with explicit content and templates
- Edit, comment, assign, and close
- Dependencies and blockers

## Inspect and search

```bash
fj --style minimal issue search --repo example.org/demo/widget --state open --page 1
fj --style minimal issue search 'timeout' --repo example.org/demo/widget --state all --all
fj issue search --repo example.org/demo/widget --labels bug --creator author --assignee maintainer
fj issue view 'example.org/demo/widget#42'
fj issue view 'example.org/demo/widget#42' comments
fj issue view 'example.org/demo/widget#42' comment 0
fj issue view 'example.org/demo/widget#42' assignees
fj issue templates --repo example.org/demo/widget
fj repo labels example.org/demo/widget view
fj milestone search --repo example.org/demo/widget --state all
```

Search supports a positional query and `--labels`, `--creator`, `--assignee`, `--milestones`, `--state`, `--page`, and `--all`. Label/milestone filters accept comma-separated strings in this baseline. Explicitly request closed/all states when needed. A single search page is not an exhaustive list.

Comment indices are zero-based positions in the fetched comments, not the issue number or API comment ID. Inspect comments immediately before editing one; do not guess indices. `issue view` may render a PR if the number refers to a PR.

## Create with explicit content and templates

Write a UTF-8 Markdown body file using the host's file-writing tool. Inspect templates and the repository's blank-issue policy first.

For an explicitly allowed blank issue:

```bash
fj issue create 'Handle request timeouts' --repo example.org/demo/widget --body-file issue.md --no-template
```

For a required template:

```bash
fj issue create 'Handle request timeouts' --repo example.org/demo/widget --template bug-report --body-file issue-form.md
```

Template details matter:

- The checked source looks for `<template>.<md|yml|yaml>` in supported template directories. Use the listed template identifier/stem (e.g. `bug-report`), not a guessed full filename copied from old wiki prose. Inspect the actual repository template if uncertain.
- Markdown templates accept an explicit completed body; omitting it opens an editor with the template content.
- YAML issue forms parse a particular generated Markdown form. A supplied body must satisfy that structure and required fields. Inspect the template and parser/version guidance; do not assume arbitrary Markdown or JSON satisfies it. If the form cannot be completed safely noninteractively, explain the limitation and use an authorized interactive path instead of bypassing policy.
- `--no-template` cannot override disabled blank issues.
- `--body` also exists for short content. Use only one of `--body` and `--body-file`; providing both is not a portable precedence contract.
- `--milestone` is accepted on create, but the checked blank-issue path does not apply it. Verify membership after creation; if requested and missing, set it explicitly with `issue edit ... milestone`.

Read back the created issue using its returned number. If creation times out, search/read before trying again.

## Edit, comment, assign, and close

Only run mutations that match the user's request. Supply content to avoid opening an editor.

```bash
fj issue edit 'example.org/demo/widget#42' title 'Handle request timeouts consistently'
fj issue edit 'example.org/demo/widget#42' body 'Replacement issue body'
fj issue comment 'example.org/demo/widget#42' --body-file comment.md
fj issue edit 'example.org/demo/widget#42' comment 0 'Replacement comment text'
fj issue edit 'example.org/demo/widget#42' labels --add bug --rm needs-triage
fj issue edit 'example.org/demo/widget#42' milestone 'v1.2'
fj issue edit 'example.org/demo/widget#42' milestone --unset
fj issue assign 'example.org/demo/widget#42' maintainer
fj issue unassign 'example.org/demo/widget#42' maintainer
fj issue close 'example.org/demo/widget#42' --with-msg 'Fixed in the released version.'
```

- Body edits replace the full body, not append to it. Read existing content and preserve unrelated material.
- Label flags are repeatable; use exact discovered names. Unknown label names may be silently ignored in the checked source. Read back labels after changes (the issue view includes them).
- Passing bare `--with-msg` opens an editor; omit the flag for no comment or provide its full value.
- Do not invent `issue reopen` or `issue delete`; neither is exposed in the checked command tree. Check current help and explain unsupported operations rather than silently switching tools or reusing a GitHub CLI.

## Dependencies and blockers

```bash
fj issue depend list 'example.org/demo/widget#42'
fj issue depend add 'example.org/demo/widget#42' 'example.org/demo/widget#41'
fj issue depend remove 'example.org/demo/widget#42' 'example.org/demo/widget#41'
fj issue block list 'example.org/demo/widget#42'
fj issue block add 'example.org/demo/widget#42' 'example.org/demo/widget#44'
fj issue block remove 'example.org/demo/widget#42' 'example.org/demo/widget#44'
```

`depend add A B` means **A depends on B**. `block add A B` means **A blocks B**. Targets can include PRs. Multiple targets are allowed, but cross-instance relationships must not be assumed supported. Read the resulting relationships to verify direction.
