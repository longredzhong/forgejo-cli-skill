#!/usr/bin/env python3
"""Build an allowlisted, deterministic ZIP and SHA-256 manifest, offline."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "forgejo-cli"
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")


def package_version(root):
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    version = package["version"]
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("Release version must be a stable MAJOR.MINOR.PATCH version")
    return version


def validate_tag(root, version, tag):
    if tag != f"v{version}":
        raise ValueError(f"Tag must match package.json version exactly: v{version}")
    tagged = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"], cwd=root, text=True
    ).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if tagged != head:
        raise ValueError("Release tag must point to the checked-out HEAD commit")


def payload_files(source):
    for directory in (source, source / "references"):
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"Expected a real skill directory: {directory}")
    if sorted(path.name for path in source.iterdir()) != ["SKILL.md", "references"]:
        raise ValueError("Unexpected files in skill root; expected SKILL.md and references only")
    references = sorted((source / "references").iterdir())
    if not references or any(not re.fullmatch(r"[a-z0-9-]+\.md", path.name) for path in references):
        raise ValueError("Expected nonempty Markdown references")
    files = [source / "SKILL.md", *references]
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Refusing nonregular payload file: {path}")
    return files


def build_release(root, output, tag=None):
    version = package_version(root)
    if tag is not None:
        validate_tag(root, version, tag)
    source = root / "skills" / SKILL_NAME
    files = payload_files(source)
    archive_name = f"forgejo-cli-skill-{version}.zip"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = f"{SKILL_NAME}/{path.relative_to(source).as_posix()}"
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, path.read_bytes(), compresslevel=9)
    data = buffer.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / archive_name
    manifest_path = output / "SHA256SUMS"
    # Never silently overwrite prior build outputs, including symlinks.
    for path in (archive_path, manifest_path):
        if path.exists() or path.is_symlink():
            raise ValueError(f"Output already exists; choose a fresh directory: {path}")
    with archive_path.open("xb") as handle:
        handle.write(data)
    with manifest_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{digest}  {archive_name}\n")
    return {"version": version, "archive": str(archive_path), "sha256": digest, "files": len(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--tag", help="Require vVERSION to match package.json and point to HEAD")
    args = parser.parse_args()
    try:
        print(json.dumps(build_release(ROOT, args.output, args.tag), indent=2))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"build_release: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
