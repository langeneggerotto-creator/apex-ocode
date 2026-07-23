import { readdir, readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  let files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files = files.concat(await walk(full));
    } else {
      files.push(full);
    }
  }
  return files;
}

function sha256(data) {
  return createHash('sha256').update(data).digest('hex');
}

export async function snapshotWorkspace(root) {
  const fileList = await walk(root);
  const snapshot = [];

  for (const file of fileList) {
    const content = await readFile(file);
    const stats = await stat(file);
    snapshot.push({
      path: path.relative(root, file),
      size: stats.size,
      hash: sha256(content)
    });
  }

  const overallHash = sha256(JSON.stringify(snapshot.sort((a,b)=>a.path.localeCompare(b.path))));

  return { files: snapshot, hash: overallHash };
}
