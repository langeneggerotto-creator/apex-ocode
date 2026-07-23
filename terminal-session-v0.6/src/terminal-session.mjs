import { createHash, randomUUID } from 'node:crypto';
import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';

const DEFAULT_ALLOWED_COMMANDS = Object.freeze([
  'git',
  'node',
  'npm',
  'npx',
  'pnpm',
  'python',
  'python3',
  'pytest'
]);

const DEFAULT_ALLOWED_SHELLS = Object.freeze(['bash', 'sh', 'pwsh']);
const FORBIDDEN_SHELL_SYNTAX = /(?:&&|\|\||[;|<>`]|\$\(|\r|\n)/u;

function stableJson(value) {
  if (Array.isArray(value)) {
    return `[${value.map(stableJson).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

function assertNonEmptyString(value, field) {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new TypeError(`${field} must be a non-empty string`);
  }
}

export function resolveWorkspacePath(workspaceRoot, requestedPath = '.') {
  assertNonEmptyString(workspaceRoot, 'workspaceRoot');
  assertNonEmptyString(requestedPath, 'requestedPath');

  if (path.isAbsolute(requestedPath)) {
    throw new Error('Absolute terminal working directories are denied');
  }

  const root = path.resolve(workspaceRoot);
  const resolved = path.resolve(root, requestedPath);
  const relative = path.relative(root, resolved);

  if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error('Terminal working directory escapes the trusted workspace');
  }

  return resolved;
}

export function inspectCommand(command, allowedCommands = DEFAULT_ALLOWED_COMMANDS) {
  assertNonEmptyString(command, 'command');

  const normalized = command.trim();
  if (FORBIDDEN_SHELL_SYNTAX.test(normalized)) {
    return {
      allowed: false,
      reason: 'SHELL_CONTROL_SYNTAX_DENIED',
      executable: null
    };
  }

  const [executable] = normalized.split(/\s+/u);
  if (!allowedCommands.includes(executable)) {
    return {
      allowed: false,
      reason: 'EXECUTABLE_NOT_ALLOWLISTED',
      executable
    };
  }

  return {
    allowed: true,
    reason: 'ALLOWLIST_MATCH',
    executable
  };
}

export class TerminalSessionStore {
  constructor({
    workspaceRoot,
    stateFile,
    allowedCommands = DEFAULT_ALLOWED_COMMANDS,
    allowedShells = DEFAULT_ALLOWED_SHELLS,
    clock = () => new Date().toISOString(),
    idFactory = () => randomUUID()
  }) {
    assertNonEmptyString(workspaceRoot, 'workspaceRoot');
    assertNonEmptyString(stateFile, 'stateFile');

    this.workspaceRoot = path.resolve(workspaceRoot);
    this.stateFile = path.resolve(stateFile);
    this.allowedCommands = [...allowedCommands];
    this.allowedShells = [...allowedShells];
    this.clock = clock;
    this.idFactory = idFactory;
    this.state = {
      schemaVersion: 'ocode.terminal-session-store.v0.6',
      sessions: {},
      events: []
    };
  }

  async load() {
    try {
      const parsed = JSON.parse(await readFile(this.stateFile, 'utf8'));
      if (parsed.schemaVersion !== 'ocode.terminal-session-store.v0.6') {
        throw new Error('Unsupported terminal session store schema');
      }
      this.state = parsed;
    } catch (error) {
      if (error?.code !== 'ENOENT') {
        throw error;
      }
    }
    return this.snapshot();
  }

  snapshot() {
    return structuredClone(this.state);
  }

  getSession(sessionId) {
    const session = this.state.sessions[sessionId];
    if (!session) {
      throw new Error(`Unknown terminal session: ${sessionId}`);
    }
    return structuredClone(session);
  }

  async createSession({ cwd = '.', shell = 'sh' } = {}) {
    if (!this.allowedShells.includes(shell)) {
      throw new Error(`Shell is not allowlisted: ${shell}`);
    }

    const resolvedCwd = resolveWorkspacePath(this.workspaceRoot, cwd);
    const now = this.clock();
    const session = {
      id: this.idFactory(),
      status: 'ACTIVE',
      shell,
      cwd: resolvedCwd,
      createdAt: now,
      updatedAt: now,
      closedAt: null,
      commands: [],
      transcript: []
    };

    if (this.state.sessions[session.id]) {
      throw new Error(`Duplicate terminal session id: ${session.id}`);
    }

    this.state.sessions[session.id] = session;
    this.#appendEvent('SESSION_CREATED', session.id, { shell, cwd: resolvedCwd });
    await this.#persist();
    return structuredClone(session);
  }

  async admitCommand(sessionId, command) {
    const session = this.#activeSession(sessionId);
    const decision = inspectCommand(command, this.allowedCommands);
    const record = {
      command: command.trim(),
      executable: decision.executable,
      decision: decision.allowed ? 'ALLOW' : 'DENY',
      reason: decision.reason,
      recordedAt: this.clock()
    };

    session.commands.push(record);
    session.updatedAt = record.recordedAt;
    this.#appendEvent('COMMAND_ADMISSION_RECORDED', sessionId, record);
    await this.#persist();
    return structuredClone(record);
  }

  async appendOutput(sessionId, { stream = 'stdout', text }) {
    const session = this.#activeSession(sessionId);
    if (!['stdout', 'stderr', 'system'].includes(stream)) {
      throw new Error(`Unsupported transcript stream: ${stream}`);
    }
    assertNonEmptyString(text, 'text');

    const entry = {
      sequence: session.transcript.length + 1,
      stream,
      text,
      recordedAt: this.clock()
    };
    session.transcript.push(entry);
    session.updatedAt = entry.recordedAt;
    this.#appendEvent('TRANSCRIPT_APPENDED', sessionId, {
      sequence: entry.sequence,
      stream,
      textSha256: sha256(text)
    });
    await this.#persist();
    return structuredClone(entry);
  }

  async closeSession(sessionId) {
    const session = this.#activeSession(sessionId);
    const now = this.clock();
    session.status = 'CLOSED';
    session.closedAt = now;
    session.updatedAt = now;
    this.#appendEvent('SESSION_CLOSED', sessionId, {});
    await this.#persist();
    return structuredClone(session);
  }

  verifyEventChain() {
    let previousHash = null;
    for (const event of this.state.events) {
      const { hash, ...unsigned } = event;
      if (unsigned.previousHash !== previousHash) {
        return false;
      }
      if (sha256(stableJson(unsigned)) !== hash) {
        return false;
      }
      previousHash = hash;
    }
    return true;
  }

  #activeSession(sessionId) {
    const session = this.state.sessions[sessionId];
    if (!session) {
      throw new Error(`Unknown terminal session: ${sessionId}`);
    }
    if (session.status !== 'ACTIVE') {
      throw new Error(`Terminal session is not active: ${sessionId}`);
    }
    return session;
  }

  #appendEvent(type, sessionId, payload) {
    const previousHash = this.state.events.at(-1)?.hash ?? null;
    const unsigned = {
      sequence: this.state.events.length + 1,
      type,
      sessionId,
      payload,
      recordedAt: this.clock(),
      previousHash
    };
    this.state.events.push({
      ...unsigned,
      hash: sha256(stableJson(unsigned))
    });
  }

  async #persist() {
    await mkdir(path.dirname(this.stateFile), { recursive: true });
    const temporaryFile = `${this.stateFile}.${process.pid}.tmp`;
    await writeFile(temporaryFile, `${JSON.stringify(this.state, null, 2)}\n`, 'utf8');
    await rename(temporaryFile, this.stateFile);
  }
}

export const terminalPolicyDefaults = Object.freeze({
  allowedCommands: DEFAULT_ALLOWED_COMMANDS,
  allowedShells: DEFAULT_ALLOWED_SHELLS
});
