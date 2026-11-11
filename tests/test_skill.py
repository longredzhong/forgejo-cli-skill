"""Offline repository checks; opt-in CLI tests invoke help, never operations.

No third-party packages are required. The frontmatter reader intentionally
supports this project's string fields and metadata mapping, not arbitrary YAML.
"""

import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "forgejo-cli"


def read_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Unterminated frontmatter") from exc
    fields = {}
    in_metadata = False
    for line in lines[1:end]:
        if line == "metadata:":
            if "metadata" in fields:
                raise ValueError("Duplicate frontmatter key: metadata")
            fields["metadata"] = {}
            in_metadata = True
            continue
        if line.startswith("  "):
            if not in_metadata:
                raise ValueError("Indented fields are only supported inside metadata")
            target = fields["metadata"]
            line = line[2:]
        else:
            in_metadata = False
            target = fields
        match = re.fullmatch(r"([a-z][a-z0-9-]*): (.+)", line)
        if not match:
            raise ValueError("Use one-line string fields or a two-space metadata mapping")
        key, value = match.groups()
        if key == "metadata" and target is fields:
            raise ValueError("metadata must be a string-to-string mapping")
        if key in target:
            raise ValueError(f"Duplicate frontmatter key: {key}")
        # Require quoted metadata so YAML booleans/numbers cannot be mistaken
        # for strings by this deliberately limited project-specific reader.
        if target is not fields and not value.startswith('"'):
            raise ValueError(f"Quote the metadata string value for {key}")
        # JSON double-quoted strings are also valid YAML strings.
        if value.startswith('"'):
            value = json.loads(value)
        elif not re.fullmatch(r"[a-z0-9-]+", value):
            raise ValueError(f"Quote the string value for {key}")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Expected a nonempty string for {key}")
        target[key] = value
    if "metadata" in fields and not fields["metadata"]:
        raise ValueError("metadata must contain string fields in this project")
    return fields, "\n".join(lines[end + 1 :])


def shell_commands(path):
    """Extract standalone fj commands, rejecting shell expansion/operators.

    Only shlex-split literal argv are returned. Nothing is evaluated by a shell.
    This intentionally refuses richer syntax instead of silently skipping it.
    """
    text = path.read_text(encoding="utf-8")
    for block in re.findall(r"^```(?:bash|sh)\n(.*?)^```", text, re.M | re.S):
        for line in block.splitlines():
            line = line.strip()
            if not line.startswith("fj "):
                continue
            if any(char in line for char in ("$", "`", "\\")):
                raise ValueError(f"Nonliteral shell example in {path.name}: {line}")
            argv = shlex.split(line, comments=True)
            if any(arg in {"|", "||", "&&", ";", "<", ">", ">>", "--"} for arg in argv):
                raise ValueError(f"Shell operator/end-of-options in {path.name}: {line}")
            yield argv


class SkillStructureTests(unittest.TestCase):
    def test_frontmatter_and_size(self):
        fields, body = read_frontmatter(SKILL / "SKILL.md")
        self.assertEqual(set(fields), {"name", "description", "compatibility", "metadata"})
        name = fields["name"]
        self.assertRegex(name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(name), 64)
        self.assertEqual(name, SKILL.name)
        self.assertLessEqual(len(fields["description"]), 1024)
        self.assertLessEqual(len(fields["compatibility"]), 500)
        self.assertTrue(body.strip())
        self.assertLess(len((SKILL / "SKILL.md").read_text().splitlines()), 500)

    def test_metadata_matches_package_and_preserves_provenance(self):
        fields, _ = read_frontmatter(SKILL / "SKILL.md")
        metadata = fields["metadata"]
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(set(metadata), {"version", "repository", "upstream-project", "tested-cli-version"})
        self.assertTrue(all(isinstance(key, str) and isinstance(value, str)
                            for key, value in metadata.items()))
        self.assertEqual(metadata["version"], package["version"])
        repository = package["repository"]["url"].removeprefix("git+").removesuffix(".git")
        self.assertEqual(metadata["repository"], repository)
        self.assertEqual(metadata["upstream-project"], "https://codeberg.org/forgejo-contrib/forgejo-cli")
        self.assertEqual(metadata["tested-cli-version"], "0.8.0-dev")
        self.assertIn("No Node.js or Python", fields["compatibility"])

    def test_metadata_parser_accepts_mapping_before_other_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "SKILL.md"
            path.write_text('---\nmetadata:\n  version: "0.1.0"\nname: test\n---\nbody\n', encoding="utf-8")
            fields, body = read_frontmatter(path)
            self.assertEqual(fields, {"metadata": {"version": "0.1.0"}, "name": "test"})
            self.assertEqual(body.strip(), "body")

    def test_metadata_parser_rejects_invalid_maps(self):
        malformed = (
            'metadata: "not a map"',
            'metadata:',
            'metadata:\n  version: "0.1.0"\n  version: "0.2.0"',
            'metadata:\n  version: "0.1.0"\nmetadata:\n  author: test',
            'metadata:\n  version: ["0.1.0"]',
            'metadata:\n  version: 0.1.0',
            'metadata:\n    version: "0.1.0"',
            '  version: "0.1.0"',
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "SKILL.md"
            for content in malformed:
                path.write_text(f"---\n{content}\n---\nbody\n", encoding="utf-8")
                with self.subTest(content=content), self.assertRaises(ValueError):
                    read_frontmatter(path)

    def test_local_markdown_links_exist_and_stay_in_repository(self):
        # Inline links in this repository deliberately use simple relative paths.
        for source in ROOT.rglob("*.md"):
            if ".git" in source.parts:
                continue
            for target in re.findall(r"\]\(([^\s)]+)\)", source.read_text(encoding="utf-8")):
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                with self.subTest(source=source.relative_to(ROOT), target=target):
                    resolved = (source.parent / unquote(parsed.path)).resolve()
                    self.assertTrue(resolved.is_relative_to(ROOT), "Link escapes repository")
                    self.assertTrue(resolved.is_file(), "Broken local file link")

    def test_references_are_directly_reachable_from_entrypoint(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        references = list((SKILL / "references").glob("*.md"))
        self.assertTrue(references)
        for path in references:
            with self.subTest(reference=path.name):
                relative = path.relative_to(SKILL).as_posix()
                self.assertIn(f"]({relative})", text)
                self.assertTrue(path.read_text(encoding="utf-8").startswith("# "))
                self.assertLess(len(path.read_text(encoding="utf-8").splitlines()), 500)

    def test_shell_examples_have_literal_argv(self):
        examples = [argv for path in SKILL.rglob("*.md") for argv in shell_commands(path)]
        self.assertGreater(len(examples), 50)
        self.assertTrue(all(argv[0] == "fj" for argv in examples))

    def test_frontmatter_reader_rejects_duplicates_and_missing_delimiter(self):
        malformed = (
            "name: test\n",
            "---\nname: test\n",
            "---\nname: test\nname: test\n---\nbody\n",
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "SKILL.md"
            for content in malformed:
                path.write_text(content, encoding="utf-8")
                with self.subTest(content=content), self.assertRaises(ValueError):
                    read_frontmatter(path)

    def test_shell_extractor_rejects_executable_expansion(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "example.md"
            path.write_text('```bash\nfj pr comment 1 "$(touch sentinel)"\n```\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                list(shell_commands(path))

    def test_evaluation_scenarios(self):
        scenarios = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(scenarios), 8)
        ids = [scenario["id"] for scenario in scenarios]
        self.assertEqual(len(ids), len(set(ids)))
        for scenario in scenarios:
            with self.subTest(scenario=scenario["id"]):
                self.assertTrue(scenario["prompt"].strip())
                self.assertTrue(scenario["context"].strip())
                self.assertTrue(scenario["expected"])
                self.assertTrue(scenario["forbidden"])
                self.assertTrue(all(isinstance(item, str) and item.strip()
                                    for item in scenario["expected"] + scenario["forbidden"]))


@unittest.skipUnless(os.environ.get("FJ_SKILL_CLI_CHECK") == "1", "Opt in with FJ_SKILL_CLI_CHECK=1")
class InstalledCliHelpTests(unittest.TestCase):
    def test_documented_commands_parse_as_help(self):
        executable = shutil.which("fj")
        self.assertIsNotNone(executable, "CLI check requested but fj is not on PATH")
        commands = sorted({tuple(argv) for path in SKILL.rglob("*.md") for argv in shell_commands(path)})
        with tempfile.TemporaryDirectory(prefix="fj-skill-help-") as temp:
            # Do not inherit user configuration, credentials, fallback hosts, or
            # Git environment. --help exits during argument parsing, before fj
            # loads keys, changes cwd, opens an editor, or calls an API.
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": temp,
                "XDG_DATA_HOME": temp,
                "XDG_CONFIG_HOME": temp,
                "XDG_CACHE_HOME": temp,
                "LC_MESSAGES": "C",
                "LANG": "C",
            }
            for argv in commands:
                with self.subTest(command=shlex.join(argv)):
                    result = subprocess.run(
                        [executable, *argv[1:], "--help"],
                        cwd=temp, env=env, stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, timeout=10, check=False,
                    )
                    output = result.stdout + result.stderr
                    self.assertEqual(result.returncode, 0, output)
                    self.assertIn("Usage:", output)
            print(f"\nChecked {len(commands)} distinct documented fj help invocations (no remote operations).")


if __name__ == "__main__":
    unittest.main()
