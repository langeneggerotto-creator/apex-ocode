import { writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

export async function restoreSnapshot(root, snapshot) {
  for (const file of snapshot.files) {
    const full = path.join(root, file.path);
    await mkdir(path.dirname(full), { recursive: true });
    await writeFile(full, ''); // placeholder (content restore not yet implemented)
  }
}
