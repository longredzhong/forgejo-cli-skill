import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, readdir, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { installSkill, payloadFiles } from '../lib/install.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const source = join(root, 'skills/forgejo-cli');
const cli = join(root, 'bin/forgejo-cli-skill.mjs');

async function workspace(t) {
  const directory = await mkdtemp(join(tmpdir(), 'fj-skill-install-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  return directory;
}

async function fixture(parent) {
  const directory = join(parent, 'source');
  await mkdir(join(directory, 'references'), { recursive: true });
  await writeFile(join(directory, 'SKILL.md'), '---\nname: forgejo-cli\n---\n');
  await writeFile(join(directory, 'references/test.md'), '# Test\n');
  return directory;
}

test('help and version do not require an install directory', () => {
  assert.match(execFileSync(process.execPath, [cli, '--help'], { encoding: 'utf8' }), /--dir/);
  const version = JSON.parse(execFileSync(process.execPath, ['-p', 'JSON.stringify(require("./package.json").version)'], { cwd: root, encoding: 'utf8' }));
  assert.equal(execFileSync(process.execPath, [cli, '--version'], { encoding: 'utf8' }).trim(), version);
});

test('requires an explicit directory and rejects unknown/repeated arguments', () => {
  for (const args of [
    ['install'], ['install', '--dir'], ['install', '--dir', '--dry-run'],
    ['install', '--force'], ['remove'], ['install', '--dir', 'a', '--dir', 'b'],
  ]) {
    const result = spawnSync(process.execPath, [cli, ...args], { cwd: root, encoding: 'utf8' });
    assert.equal(result.status, 1, JSON.stringify(args));
    assert.match(result.stderr, /forgejo-cli-skill:/);
  }
});

test('dry-run does not create parent directories', async t => {
  const temp = await workspace(t);
  const directory = join(temp, 'missing/skills');
  const result = await installSkill({ source, directory, dryRun: true });
  assert.equal(result.destination, join(directory, 'forgejo-cli'));
  await assert.rejects(readdir(directory), { code: 'ENOENT' });
});

test('copies the complete allowlisted payload from any working directory', async t => {
  const temp = await workspace(t);
  const directory = join(temp, 'space in path/skills');
  const result = spawnSync(process.execPath, [cli, 'install', '--dir', directory], {
    cwd: temp, encoding: 'utf8', env: { ...process.env, HOME: temp },
  });
  assert.equal(result.status, 0, result.stderr);
  for (const file of await payloadFiles(source)) {
    assert.deepEqual(await readFile(join(directory, 'forgejo-cli', file)), await readFile(join(source, file)));
  }
  assert.deepEqual((await readdir(join(directory, 'forgejo-cli'))).sort(), ['SKILL.md', 'references']);
});

test('refuses an existing skill and preserves its contents', async t => {
  const temp = await workspace(t);
  const destination = join(temp, 'forgejo-cli');
  await mkdir(destination);
  await writeFile(join(destination, 'user.md'), 'keep');
  await assert.rejects(installSkill({ source, directory: temp }), /already exists/);
  assert.equal(await readFile(join(destination, 'user.md'), 'utf8'), 'keep');
  assert.deepEqual(await readdir(destination), ['user.md']);
});

test('refuses an existing file destination', async t => {
  const temp = await workspace(t);
  await writeFile(join(temp, 'forgejo-cli'), 'keep');
  await assert.rejects(installSkill({ source, directory: temp }), /already exists/);
  assert.equal(await readFile(join(temp, 'forgejo-cli'), 'utf8'), 'keep');
});

test('refuses a dangling destination symlink', { skip: process.platform === 'win32' }, async t => {
  const temp = await workspace(t);
  await symlink(join(temp, 'missing'), join(temp, 'forgejo-cli'));
  await assert.rejects(installSkill({ source, directory: temp }), /already exists/);
  await assert.rejects(readdir(join(temp, 'missing')), { code: 'ENOENT' });
});

test('only one concurrent install may reserve the destination', async t => {
  const temp = await workspace(t);
  const results = await Promise.allSettled([
    installSkill({ source, directory: temp }), installSkill({ source, directory: temp }),
  ]);
  assert.equal(results.filter(result => result.status === 'fulfilled').length, 1);
  assert.equal(results.filter(result => result.status === 'rejected').length, 1);
  assert.deepEqual(await readFile(join(temp, 'forgejo-cli/SKILL.md')), await readFile(join(source, 'SKILL.md')));
});

test('rejects the skill folder itself as the parent directory', async t => {
  const temp = await workspace(t);
  await assert.rejects(installSkill({ source, directory: join(temp, 'forgejo-cli') }), /parent skills directory/);
});

test('rejects symlinked payload files before writing', { skip: process.platform === 'win32' }, async t => {
  const temp = await workspace(t);
  const fake = await fixture(temp);
  await rm(join(fake, 'references/test.md'));
  await symlink(join(fake, 'SKILL.md'), join(fake, 'references/test.md'));
  const directory = join(temp, 'target');
  await assert.rejects(installSkill({ source: fake, directory }), /nonregular/);
  await assert.rejects(readdir(directory), { code: 'ENOENT' });
});

test('rejects unexpected files instead of copying them', async t => {
  const temp = await workspace(t);
  const fake = await fixture(temp);
  await writeFile(join(fake, 'keys.json'), 'not a credential');
  await assert.rejects(payloadFiles(fake), /Unexpected files/);
});
