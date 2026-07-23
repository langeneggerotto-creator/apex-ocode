import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

export async function captureSnapshot(workspacePath, files) {
  const snapshot = {};
  for (const file of files) {
    const fullPath = path.join(workspacePath, file);
    try {
      const content = await readFile(fullPath, 'utf8');
      snapshot[file] = content;
    } catch {
      snapshot[file] = null;
    }
  }
  return snapshot;
}

export async function restoreSnapshot(workspacePath, snapshot) {
  for (const [file, content] of Object.entries(snapshot)) {
    const fullPath = path.join(workspacePath, file);
    if (content === null) continue;
    await mkdir(path.dirname(fullPath), { recursive: true });
    await writeFile(fullPath, content, 'utf8');
  }
}

export function computeDiff(before, after) {
  const created = [];
  const modified = [];
  const deleted = [];

  const allFiles = new Set([...Object.keys(before), ...Object.keys(after)]);

  for (const file of allFiles) {
    if (!(file in before)) created.push(file);
    else if (!(file in after)) deleted.push(file);
    else if (before[file] !== after[file]) modified.push(file);
  }

  return { created, modified, deleted };
}
