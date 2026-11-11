"""Distribution integration tests use temporary outputs and offline npm only."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_release", ROOT / "scripts" / "build_release.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class ZipDistributionTests(unittest.TestCase):
    def test_reproducible_zip_layout_bytes_and_checksum(self):
        with tempfile.TemporaryDirectory() as temp:
            results = [BUILDER.build_release(ROOT, Path(temp) / name) for name in ("one", "two")]
            first, second = [Path(result["archive"]) for result in results]
            self.assertEqual(first.read_bytes(), second.read_bytes())
            data = first.read_bytes()
            checksum = hashlib.sha256(data).hexdigest()
            self.assertEqual(results[0]["sha256"], checksum)
            self.assertEqual((first.parent / "SHA256SUMS").read_text(), f"{checksum}  {first.name}\n")
            with zipfile.ZipFile(first) as archive:
                source = ROOT / "skills" / "forgejo-cli"
                expected = {f"forgejo-cli/{path.relative_to(source).as_posix()}"
                            for path in BUILDER.payload_files(source)}
                self.assertEqual(set(archive.namelist()), expected)
                self.assertIsNone(archive.testzip())
                for entry in archive.infolist():
                    self.assertEqual(entry.date_time, (1980, 1, 1, 0, 0, 0))
                    self.assertEqual((entry.external_attr >> 16) & 0o777, 0o644)
                    path = ROOT / "skills" / entry.filename
                    self.assertEqual(archive.read(entry), path.read_bytes())

    def test_existing_outputs_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / "SHA256SUMS").write_text("preserve")
            with self.assertRaisesRegex(ValueError, "Output already exists"):
                BUILDER.build_release(ROOT, output)
            self.assertEqual((output / "SHA256SUMS").read_text(), "preserve")
            self.assertEqual(sorted(path.name for path in output.iterdir()), ["SHA256SUMS"])

    def test_invalid_tag_is_rejected_before_build(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            for tag in ("v9.9.9", "main", "../../bad", "v0.1.0;echo bad"):
                with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "Tag must match"):
                    BUILDER.build_release(ROOT, output, tag)
            self.assertFalse(output.exists())

    @unittest.skipUnless(shutil.which("git"), "Git is required for release-tag verification")
    def test_matching_tag_must_point_to_head(self):
        with tempfile.TemporaryDirectory(prefix="fj-tag-check-") as temp:
            root = Path(temp)
            env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
            git = [shutil.which("git"), "-c", "core.hooksPath=" + os.devnull,
                   "-c", "user.name=Distribution Test", "-c", "user.email=test@example.invalid",
                   "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false"]
            def run(*args):
                subprocess.run([*git, *args], cwd=root, env=env, check=True, capture_output=True)
            run("init", "--quiet")
            run("commit", "--allow-empty", "--quiet", "-m", "First test commit")
            run("tag", "v0.1.0")
            BUILDER.validate_tag(root, "0.1.0", "v0.1.0")
            run("commit", "--allow-empty", "--quiet", "-m", "Second test commit")
            with self.assertRaisesRegex(ValueError, "HEAD"):
                BUILDER.validate_tag(root, "0.1.0", "v0.1.0")

    def test_package_version_matches_lockfile(self):
        package = json.loads((ROOT / "package.json").read_text())
        lock = json.loads((ROOT / "package-lock.json").read_text())
        self.assertEqual(BUILDER.package_version(ROOT), lock["version"])
        self.assertEqual(package["version"], lock["packages"][""]["version"])
        self.assertEqual(package["name"], lock["packages"][""]["name"])

    def test_payload_rejects_unexpected_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "forgejo-cli"
            (source / "references").mkdir(parents=True)
            (source / "SKILL.md").write_text("skill")
            ref = source / "references" / "test.md"
            ref.write_text("reference")
            unwanted = source / "keys.json"
            unwanted.write_text("not a credential")
            with self.assertRaisesRegex(ValueError, "Unexpected files"):
                BUILDER.payload_files(source)
            unwanted.unlink()
            if os.name != "nt":
                ref.unlink()
                ref.symlink_to(source / "SKILL.md")
                with self.assertRaisesRegex(ValueError, "nonregular"):
                    BUILDER.payload_files(source)


@unittest.skipUnless(shutil.which("npm") and shutil.which("node"), "npm and Node are required for package smoke testing")
class NpmDistributionTests(unittest.TestCase):
    def test_actual_tarball_and_offline_npx_installation(self):
        with tempfile.TemporaryDirectory(prefix="fj-npm-smoke-") as temp:
            directory = Path(temp)
            env = {key: value for key, value in os.environ.items()
                   if not key.lower().startswith("npm_config_")
                   and key.upper() not in {"NPM_TOKEN", "NODE_AUTH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"}}
            env.update({
                "HOME": temp,
                "XDG_CONFIG_HOME": temp,
                "npm_config_cache": str(directory / "cache"),
                "npm_config_userconfig": str(directory / "npmrc"),
                "npm_config_globalconfig": str(directory / "global-npmrc"),
                "npm_config_offline": "true",
                "npm_config_ignore_scripts": "true",
                "npm_config_audit": "false",
                "npm_config_fund": "false",
            })
            packed = subprocess.run(
                [shutil.which("npm"), "pack", "--ignore-scripts", "--json", "--pack-destination", temp],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=60, check=True,
            )
            metadata = json.loads(packed.stdout)[0]
            archive_path = directory / metadata["filename"]
            package = json.loads((ROOT / "package.json").read_text())
            expected = {"package/package.json", "package/README.md", "package/README.zh-CN.md",
                        "package/bin/forgejo-cli-skill.mjs", "package/lib/install.mjs"}
            expected.update(f"package/skills/forgejo-cli/{path.relative_to(ROOT / 'skills' / 'forgejo-cli').as_posix()}"
                            for path in BUILDER.payload_files(ROOT / "skills" / "forgejo-cli"))
            with tarfile.open(archive_path, "r:gz") as archive:
                self.assertEqual(set(archive.getnames()), expected)
                self.assertTrue(all(member.isfile() for member in archive.getmembers()))
                bundled = json.load(archive.extractfile("package/package.json"))
                self.assertEqual(bundled["version"], package["version"])
                self.assertFalse(bundled.get("dependencies"))
                self.assertFalse(any(key in bundled.get("scripts", {})
                                     for key in ("preinstall", "install", "postinstall", "prepare")))
            target = directory / "installed skills"
            command = [shutil.which("npm"), "exec", "--offline", "--yes", "--ignore-scripts",
                       "--package", str(archive_path), "--", "forgejo-cli-skill", "install", "--dir", str(target)]
            result = subprocess.run(command, cwd=temp, env=env, text=True, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Installed", result.stdout)
            for source in BUILDER.payload_files(ROOT / "skills" / "forgejo-cli"):
                relative = source.relative_to(ROOT / "skills")
                self.assertEqual((target / relative).read_bytes(), source.read_bytes())
            again = subprocess.run(command, cwd=temp, env=env, text=True, capture_output=True, timeout=60)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("already exists", again.stderr)


if __name__ == "__main__":
    unittest.main()
