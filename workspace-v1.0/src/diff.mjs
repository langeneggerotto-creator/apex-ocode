export function diffSnapshots(before, after) {
  const beforeMap = new Map(before.files.map(f => [f.path, f]));
  const afterMap = new Map(after.files.map(f => [f.path, f]));

  const created = [];
  const modified = [];
  const deleted = [];

  for (const [path, file] of afterMap) {
    if (!beforeMap.has(path)) {
      created.push(path);
    } else if (beforeMap.get(path).hash !== file.hash) {
      modified.push(path);
    }
  }

  for (const [path] of beforeMap) {
    if (!afterMap.has(path)) {
      deleted.push(path);
    }
  }

  return { created, modified, deleted };
}
