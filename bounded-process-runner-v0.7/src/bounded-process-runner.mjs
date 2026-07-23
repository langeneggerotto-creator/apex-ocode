import { constants as fsConstants } from 'node:fs';
import { access, mkdtemp, realpath, rm, stat } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';

import { resolveWorkspacePath } from '../../terminal-session-v0.6/src/terminal-session.mjs';

const DEFAULT_TIMEOUT_MS = 5_000;
const DEFAULT_OUTPUT_LIMIT_BYTES = 64 * 1024;
const DEFAULT_KILL_GRACE_MS = 200;
const SUPPORTED_TOOLCHAIN_ROOTS = Object.freeze(['/usr', '/opt', '/bin', '/sbin']);
const SAFE_TOKEN = /^[^\0\r\n]*$/u;

const LINUX_SANDBOX_SCRIPT = String.raw`
set -eu
root=$1
workspace=$2
sandbox_cwd=$3
executable=$4
tool_dir=$(dirname "$executable")
shift 4

setup_failed() {
  code=$?
  printf 'OCODE_SANDBOX_SETUP_FAILED:%s\n' "$code" >&2
  exit 125
}
trap setup_failed EXIT

mount --make-rprivate /
mkdir -p "$root/workspace" "$root/usr" "$root/opt" "$root/etc" "$root/tmp" "$root/dev"

bind_read_only_dir() {
  source_path=$1
  target_path="$root$source_path"
  if [ -d "$source_path" ]; then
    mkdir -p "$target_path"
    mount --bind "$source_path" "$target_path"
    mount -o remount,bind,ro "$target_path"
  fi
}

mirror_host_path() {
  source_path=$1
  target_path="$root$source_path"
  if [ -L "$source_path" ]; then
    mkdir -p "$(dirname "$target_path")"
    ln -s "$(readlink "$source_path")" "$target_path"
  elif [ -d "$source_path" ]; then
    mkdir -p "$target_path"
    mount --bind "$source_path" "$target_path"
    mount -o remount,bind,ro "$target_path"
  fi
}

bind_read_only_dir /usr
bind_read_only_dir /opt
mirror_host_path /bin
mirror_host_path /sbin
mirror_host_path /lib
mirror_host_path /lib64

mount --bind "$workspace" "$root/workspace"
mount -t tmpfs -o size=16m,nosuid,nodev,noexec tmpfs "$root/tmp"

: > "$root/dev/null"
mount --bind /dev/null "$root/dev/null"

printf 'root:x:0:0:OCODE Sandbox:/workspace:/bin/sh\n' > "$root/etc/passwd"
printf 'root:x:0:\n' > "$root/etc/group"
printf 'hosts: files\n' > "$root/etc/nsswitch.conf"

trap - EXIT
exec /usr/sbin/chroot "$root" /usr/bin/env -i \
  PATH="$tool_dir:/usr/local/bin:/usr/bin:/bin" \
  HOME=/workspace \
  TMPDIR=/tmp \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  /bin/sh -c 'cd "$1"; shift; exec "$@"' sh "$sandbox_cwd" "$executable" "$@"
`;

function assertPositiveInteger(value, field) {
  if (!Number.isInteger(value) || value <= 0) {
    throw new TypeError(`${field} must be a positive integer`);
  }
}

function assertSafeToken(value, field) {
  if (typeof value !== 'string' || value.length === 0 || !SAFE_TOKEN.test(value)) {
    throw new TypeError(`${field} must be a non-empty string without NUL or line breaks`);
  }
}

function isPathWithin(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === '' || (!path.isAbsolute(relative) && relative !== '..' && !relative.startsWith(`..${path.sep}`));
}

async function findExecutable(executable, searchPath = process.env.PATH ?? '') {
  assertSafeToken(executable, 'executable');
  if (executable.includes('/') || executable.includes('\\')) {
    throw new Error('Executable paths are denied; use an allowlisted executable name');
  }

  for (const directory of searchPath.split(path.delimiter).filter(Boolean)) {
    const candidate = path.join(directory, executable);
    try {
      await access(candidate, fsConstants.X_OK);
      return await realpath(candidate);
    } catch {
      // Continue searching PATH.
    }
  }
  throw new Error(`Executable was not found on PATH: ${executable}`);
}

function assertSupportedToolchainPath(executablePath) {
  const supported = SUPPORTED_TOOLCHAIN_ROOTS.some((root) => isPathWithin(root, executablePath));
  if (!supported) {
    throw new Error(`Executable is outside the read-only sandbox toolchain roots: ${executablePath}`);
  }
}

async function resolveExistingWorkspaceDirectory(workspaceRoot, requestedCwd) {
  const logicalRoot = path.resolve(workspaceRoot);
  const logicalCwd = resolveWorkspacePath(logicalRoot, requestedCwd);
  const physicalRoot = await realpath(logicalRoot);
  const physicalCwd = await realpath(logicalCwd);
  const metadata = await stat(physicalCwd);

  if (!metadata.isDirectory()) {
    throw new Error('Process working directory must be an existing directory');
  }
  if (!isPathWithin(physicalRoot, physicalCwd)) {
    throw new Error('Process working directory escapes the physical workspace through a symbolic link');
  }

  const relative = path.relative(physicalRoot, physicalCwd);
  return {
    physicalRoot,
    physicalCwd,
    sandboxCwd: relative === '' ? '/workspace' : `/workspace/${relative.split(path.sep).join('/')}`
  };
}

function statusFromTermination(terminationReason, exitCode, stderr) {
  if (terminationReason === 'TIMEOUT') return 'TIMED_OUT';
  if (terminationReason === 'CANCELLED') return 'CANCELLED';
  if (terminationReason === 'OUTPUT_LIMIT') return 'OUTPUT_LIMIT_EXCEEDED';
  if (stderr.includes('OCODE_SANDBOX_SETUP_FAILED:') || (exitCode !== 0 && stderr.startsWith('unshare:'))) {
    return 'SANDBOX_UNAVAILABLE';
  }
  return exitCode === 0 ? 'COMPLETED' : 'FAILED';
}

function commandForAdmission(executable, args) {
  return [executable, ...args].join(' ');
}

export class BoundedProcessRunner {
  constructor({
    workspaceRoot,
    sessionStore,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    outputLimitBytes = DEFAULT_OUTPUT_LIMIT_BYTES,
    killGraceMs = DEFAULT_KILL_GRACE_MS,
    unsharePath = '/usr/bin/unshare'
  }) {
    assertSafeToken(workspaceRoot, 'workspaceRoot');
    if (!sessionStore || typeof sessionStore.admitCommand !== 'function' || typeof sessionStore.appendOutput !== 'function') {
      throw new TypeError('sessionStore must provide admitCommand and appendOutput');
    }
    assertPositiveInteger(timeoutMs, 'timeoutMs');
    assertPositiveInteger(outputLimitBytes, 'outputLimitBytes');
    assertPositiveInteger(killGraceMs, 'killGraceMs');
    assertSafeToken(unsharePath, 'unsharePath');

    this.workspaceRoot = path.resolve(workspaceRoot);
    this.sessionStore = sessionStore;
    this.timeoutMs = timeoutMs;
    this.outputLimitBytes = outputLimitBytes;
    this.killGraceMs = killGraceMs;
    this.unsharePath = unsharePath;
  }

  async run({
    sessionId,
    executable,
    args = [],
    cwd = '.',
    network = 'deny',
    timeoutMs = this.timeoutMs,
    outputLimitBytes = this.outputLimitBytes,
    signal
  }) {
    assertSafeToken(sessionId, 'sessionId');
    assertSafeToken(executable, 'executable');
    if (!Array.isArray(args)) throw new TypeError('args must be an array');
    args.forEach((argument, index) => assertSafeToken(argument, `args[${index}]`));
    assertSafeToken(cwd, 'cwd');
    assertPositiveInteger(timeoutMs, 'timeoutMs');
    assertPositiveInteger(outputLimitBytes, 'outputLimitBytes');

    if (network !== 'deny') {
      throw new Error('NETWORK_POLICY_DENIED: v0.7 supports only default-denied networking');
    }
    if (process.platform !== 'linux') {
      throw new Error('SANDBOX_UNAVAILABLE: v0.7 requires Linux user, mount, PID, and network namespaces');
    }

    const admission = await this.sessionStore.admitCommand(
      sessionId,
      commandForAdmission(executable, args)
    );
    if (admission.decision !== 'ALLOW') {
      return {
        schemaVersion: 'ocode.bounded-process-result.v0.7',
        status: 'POLICY_DENIED',
        admission,
        network: 'DENIED_BY_POLICY',
        sandbox: 'NOT_STARTED',
        exitCode: null,
        signal: null,
        stdout: '',
        stderr: '',
        outputBytes: 0,
        outputTruncated: false,
        durationMs: 0
      };
    }

    if (signal?.aborted) {
      return {
        schemaVersion: 'ocode.bounded-process-result.v0.7',
        status: 'CANCELLED',
        admission,
        network: 'DENIED_BY_LINUX_NETWORK_NAMESPACE',
        sandbox: 'NOT_STARTED',
        exitCode: null,
        signal: null,
        stdout: '',
        stderr: '',
        outputBytes: 0,
        outputTruncated: false,
        durationMs: 0
      };
    }

    const workspace = await resolveExistingWorkspaceDirectory(this.workspaceRoot, cwd);
    const executablePath = await findExecutable(executable);
    assertSupportedToolchainPath(executablePath);
    await access(this.unsharePath, fsConstants.X_OK);

    const sandboxRoot = await mkdtemp(path.join(os.tmpdir(), 'ocode-runner-v07-'));
    const startedAt = process.hrtime.bigint();

    try {
      const childArgs = [
        '--user',
        '--map-root-user',
        '--mount',
        '--net',
        '--pid',
        '--fork',
        '--kill-child=SIGKILL',
        '/bin/sh',
        '-c',
        LINUX_SANDBOX_SCRIPT,
        'ocode-sandbox',
        sandboxRoot,
        workspace.physicalRoot,
        workspace.sandboxCwd,
        executablePath,
        ...args
      ];

      const processResult = await this.#spawnBounded({
        childArgs,
        timeoutMs,
        outputLimitBytes,
        signal
      });
      const durationMs = Number((process.hrtime.bigint() - startedAt) / 1_000_000n);
      const result = {
        schemaVersion: 'ocode.bounded-process-result.v0.7',
        status: statusFromTermination(
          processResult.terminationReason,
          processResult.exitCode,
          processResult.stderr
        ),
        admission,
        network: 'DENIED_BY_LINUX_NETWORK_NAMESPACE',
        sandbox: 'LINUX_USER_MOUNT_PID_NETWORK_NAMESPACES_WITH_CHROOT',
        exitCode: processResult.exitCode,
        signal: processResult.signal,
        stdout: processResult.stdout,
        stderr: processResult.stderr,
        outputBytes: processResult.outputBytes,
        outputTruncated: processResult.outputTruncated,
        durationMs
      };

      if (result.stdout.length > 0) {
        await this.sessionStore.appendOutput(sessionId, { stream: 'stdout', text: result.stdout });
      }
      if (result.stderr.length > 0) {
        await this.sessionStore.appendOutput(sessionId, { stream: 'stderr', text: result.stderr });
      }
      await this.sessionStore.appendOutput(sessionId, {
        stream: 'system',
        text: JSON.stringify({
          status: result.status,
          exitCode: result.exitCode,
          signal: result.signal,
          durationMs: result.durationMs,
          outputBytes: result.outputBytes,
          outputTruncated: result.outputTruncated,
          network: result.network,
          sandbox: result.sandbox
        })
      });

      return result;
    } finally {
      await rm(sandboxRoot, { recursive: true, force: true });
    }
  }

  #spawnBounded({ childArgs, timeoutMs, outputLimitBytes, signal }) {
    return new Promise((resolve, reject) => {
      const child = spawn(this.unsharePath, childArgs, {
        cwd: this.workspaceRoot,
        env: {
          PATH: process.env.PATH ?? '/usr/bin:/bin',
          LANG: 'C.UTF-8',
          LC_ALL: 'C.UTF-8'
        },
        detached: true,
        shell: false,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      let settled = false;
      let closed = false;
      let terminationReason = null;
      let outputBytes = 0;
      let outputTruncated = false;
      const stdoutChunks = [];
      const stderrChunks = [];
      let killTimer = null;

      const killProcessGroup = (killSignal) => {
        if (!child.pid || closed) return;
        try {
          process.kill(-child.pid, killSignal);
        } catch (error) {
          if (error?.code !== 'ESRCH') throw error;
        }
      };

      const terminate = (reason) => {
        if (terminationReason !== null || closed) return;
        terminationReason = reason;
        try {
          killProcessGroup('SIGTERM');
        } catch (error) {
          rejectOnce(error);
          return;
        }
        killTimer = setTimeout(() => {
          try {
            killProcessGroup('SIGKILL');
          } catch (error) {
            rejectOnce(error);
          }
        }, this.killGraceMs);
        killTimer.unref?.();
      };

      const capture = (target, chunk) => {
        const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
        const remaining = Math.max(0, outputLimitBytes - Math.min(outputBytes, outputLimitBytes));
        if (remaining > 0) target.push(buffer.subarray(0, remaining));
        outputBytes += buffer.length;
        if (outputBytes > outputLimitBytes) {
          outputTruncated = true;
          terminate('OUTPUT_LIMIT');
        }
      };

      const cleanup = () => {
        clearTimeout(timeoutTimer);
        if (killTimer) clearTimeout(killTimer);
        signal?.removeEventListener('abort', onAbort);
      };

      const rejectOnce = (error) => {
        if (settled) return;
        settled = true;
        cleanup();
        reject(error);
      };

      const onAbort = () => terminate('CANCELLED');
      const timeoutTimer = setTimeout(() => terminate('TIMEOUT'), timeoutMs);
      timeoutTimer.unref?.();
      signal?.addEventListener('abort', onAbort, { once: true });

      child.stdout.on('data', (chunk) => capture(stdoutChunks, chunk));
      child.stderr.on('data', (chunk) => capture(stderrChunks, chunk));
      child.once('error', rejectOnce);
      child.once('close', (exitCode, closeSignal) => {
        closed = true;
        if (settled) return;
        settled = true;
        cleanup();
        resolve({
          exitCode,
          signal: closeSignal,
          stdout: Buffer.concat(stdoutChunks).toString('utf8'),
          stderr: Buffer.concat(stderrChunks).toString('utf8'),
          outputBytes,
          outputTruncated,
          terminationReason
        });
      });
    });
  }
}

export const boundedRunnerDefaults = Object.freeze({
  timeoutMs: DEFAULT_TIMEOUT_MS,
  outputLimitBytes: DEFAULT_OUTPUT_LIMIT_BYTES,
  killGraceMs: DEFAULT_KILL_GRACE_MS,
  network: 'deny'
});
