import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

export function ensureDir(directory) {
  fs.mkdirSync(directory, { recursive: true });
}

export function writeText(filePath, content) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, content.endsWith('\n') ? content : `${content}\n`, 'utf8');
}

export function writeJson(filePath, value) {
  writeText(filePath, JSON.stringify(value, null, 2));
}

export function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

export function sha256(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
}

export function fileSha256(filePath) {
  return sha256(fs.readFileSync(filePath));
}

export function stableId(prefix, value) {
  return `${prefix}-${sha256(value).slice(0, 16)}`;
}

export function relativeFiles(root) {
  const results = [];
  function visit(current) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const absolute = path.join(current, entry.name);
      if (entry.isDirectory()) visit(absolute);
      else results.push(path.relative(root, absolute).replaceAll(path.sep, '/'));
    }
  }
  visit(root);
  return results.sort();
}
