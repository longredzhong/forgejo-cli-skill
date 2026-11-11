import { constants } from 'node:fs';
import { copyFile, lstat, mkdir, readdir, rmdir, unlink } from 'node:fs/promises';
import { basename, join, resolve } from 'node:path';

export const skillName = 'forgejo-cli';

// Enumerate only the portable skill payload; never copy repository/config files.
export async function payloadFiles(source) {
  for (const directory of [source, join(source, 'references')]) {
    const stat = await lstat(directory);
    if (!stat.isDirectory() || stat.isSymbolicLink()) {
      throw new Error(`Expected a real skill directory: ${directory}`);
    }
  }
  const rootEntries = (await readdir(source)).sort();
  if (rootEntries.join(',') !== 'SKILL.md,references') {
    throw new Error('Unexpected files in skill root; expected SKILL.md and references only.');
  }
  const refs = (await readdir(join(source, 'references'))).sort();
  if (!refs.length || refs.some(name => !/^[a-z0-9-]+\.md$/.test(name))) {
    throw new Error('Expected nonempty references containing only named Markdown files.');
  }
  const files = ['SKILL.md', ...refs.map(name => join('references', name))];
  for (const file of files) {
    const stat = await lstat(join(source, file));
    if (!stat.isFile() || stat.isSymbolicLink()) {
      throw new Error(`Refusing nonregular payload file: ${file}`);
    }
  }
  return files;
}

export async function installSkill({ source, directory, dryRun = false }) {
  if (!directory || !directory.trim()) throw new Error('An explicit --dir SKILLS_DIRECTORY is required.');
  const parent = resolve(directory);
  if (basename(parent) === skillName) {
    throw new Error('--dir must be the parent skills directory, not forgejo-cli itself.');
  }
  const destination = join(parent, skillName);
  const files = await payloadFiles(source);
  try {
    await lstat(destination);
    throw new Error(`Destination already exists; nothing was changed: ${destination}`);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  if (dryRun) return { destination, files, dryRun: true };

  // Exclusive mkdir reserves the destination, including against concurrent installs.
  // Existing directories or symlinks are never merged into or replaced.
  await mkdir(parent, { recursive: true });
  try {
    await mkdir(destination);
  } catch (error) {
    if (error.code === 'EEXIST') {
      throw new Error(`Destination already exists; nothing was changed: ${destination}`);
    }
    throw error;
  }
  const createdFiles = [];
  const createdDirectories = [destination];
  try {
    const references = join(destination, 'references');
    await mkdir(references);
    createdDirectories.push(references);
    for (const file of files) {
      const target = join(destination, file);
      await copyFile(join(source, file), target, constants.COPYFILE_EXCL);
      createdFiles.push(target);
    }
  } catch (error) {
    // Remove only our own copies; never recursively erase a user's directory.
    for (const file of createdFiles.reverse()) await unlink(file).catch(() => {});
    for (const directory of createdDirectories.reverse()) await rmdir(directory).catch(() => {});
    throw new Error(`Installation failed; inspect ${destination} before retrying: ${error.message}`, { cause: error });
  }
  return { destination, files, dryRun: false };
}
