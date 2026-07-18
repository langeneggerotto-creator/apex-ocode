import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

function walk(directory) {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...walk(absolute));
    } else {
      files.push(absolute);
    }
  }
  return files;
}

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function inspectExport(platform, directory) {
  if (!fs.existsSync(directory)) {
    throw new Error(`${platform} export directory is missing: ${directory}`);
  }

  const files = walk(directory);
  const bundleFiles = files.filter((file) => /\.(?:js|hbc)$/.test(file));
  if (files.length === 0) {
    throw new Error(`${platform} export is empty.`);
  }
  if (bundleFiles.length === 0) {
    throw new Error(`${platform} export does not contain a JavaScript or Hermes bundle.`);
  }

  return {
    platform,
    directory,
    file_count: files.length,
    bundle_count: bundleFiles.length,
    bundles: bundleFiles.map((file) => ({
      path: path.relative(directory, file).replaceAll('\\', '/'),
      size_bytes: fs.statSync(file).size,
      sha256: sha256(file)
    }))
  };
}

const result = {
  build: 'OCODE_UNIVERSAL_WRAPPER_v0.3.1_EXPO_BUNDLE_AND_PHONE_PREVIEW_HANDOFF',
  generated_at: new Date().toISOString(),
  truth_status: 'EXPO_NATIVE_BUNDLES_GENERATED__PHYSICAL_PHONE_INTERACTION_NOT_YET_VERIFIED',
  exports: [inspectExport('ios', 'dist-ios'), inspectExport('android', 'dist-android')],
  truth_boundary:
    'Successful Expo export proves Metro can produce platform-targeted JavaScript and asset bundles for this project. It does not prove native binary compilation, installation, launch, touch interaction, persistence on a physical phone, or production readiness.'
};

fs.mkdirSync('evidence', { recursive: true });
fs.writeFileSync('evidence/native-export-verification.json', `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(JSON.stringify(result, null, 2));
