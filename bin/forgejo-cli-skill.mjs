#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { installSkill } from '../lib/install.mjs';

const help = `forgejo-cli-skill — install the bundled fj Agent Skill

Usage:
  forgejo-cli-skill install --dir SKILLS_DIRECTORY [--dry-run]
  forgejo-cli-skill --help
  forgejo-cli-skill --version

Examples:
  forgejo-cli-skill install --dir .agents/skills
  forgejo-cli-skill install --dir ~/.agents/skills --dry-run

--dir is the parent skills directory. The installer creates forgejo-cli/ inside it.
Existing destinations are never overwritten. No fj install, login, or remote call
is performed. No install lifecycle hook runs this command automatically.
`;

try {
  const args = process.argv.slice(2);
  if (args.length === 0 || (args.length === 1 && ['--help', '-h'].includes(args[0]))) {
    process.stdout.write(help);
  } else if (args.length === 1 && args[0] === '--version') {
    const pkg = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'));
    process.stdout.write(`${pkg.version}\n`);
  } else {
    if (args.shift() !== 'install') throw new Error('Unknown command. Use --help.');
    let directory;
    let dryRun = false;
    while (args.length) {
      const arg = args.shift();
      if (arg === '--dir' && directory === undefined) {
        directory = args.shift();
        if (!directory || directory.startsWith('--')) throw new Error('--dir requires a directory path.');
      } else if (arg === '--dry-run' && !dryRun) {
        dryRun = true;
      } else {
        throw new Error(`Unknown or repeated option: ${arg}. Use --help.`);
      }
    }
    const source = fileURLToPath(new URL('../skills/forgejo-cli/', import.meta.url));
    const result = await installSkill({ source, directory, dryRun });
    process.stdout.write(`${dryRun ? 'Would install' : 'Installed'} ${result.files.length} files to ${result.destination}\n`);
  }
} catch (error) {
  process.stderr.write(`forgejo-cli-skill: ${error.message}\n`);
  process.exitCode = 1;
}
