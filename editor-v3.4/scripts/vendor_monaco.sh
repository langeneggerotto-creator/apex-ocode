#!/usr/bin/env bash
# Installs monaco-editor via npm and copies its pre-built AMD loader assets
# (min/vs) into frontend/vendor/monaco/ — no bundler needed, no runtime CDN
# dependency. Deterministic: pinned by package.json's version.
set -euo pipefail

BITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$BITE_DIR/frontend"
VENDOR_DIR="$FRONTEND_DIR/vendor/monaco"
NPM_INSTALL_DIR="$BITE_DIR/npm-install-scratch"

mkdir -p "$NPM_INSTALL_DIR"
cd "$NPM_INSTALL_DIR"
npm install --no-save --no-package-lock monaco-editor@0.56.0 >/dev/null

rm -rf "$VENDOR_DIR"
mkdir -p "$VENDOR_DIR"
cp -r node_modules/monaco-editor/min/vs "$VENDOR_DIR/vs"

echo "monaco-editor vendored to $VENDOR_DIR"
du -sh "$VENDOR_DIR"
