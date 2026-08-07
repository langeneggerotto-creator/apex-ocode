"""Hardened wrapper around the real ``git`` binary — every operation goes
through :func:`run`, so the safety flags live in exactly one place. Confined to
a workspace that must already carry Bite 1's trust marker (reused unmodified);
this module never establishes trust, only checks it before spawning any process.

Hardening, verified empirically before this file was written (see PLAN.md's
Risks section for the two non-obvious findings):

- Hooks disabled via ``core.hooksPath`` pointed at a real, empty directory
  created outside the workspace (so a malicious repo cannot populate it).
- External diff tools disabled via ``--no-ext-diff`` on the ``diff``
  subcommand — ``-c diff.external=`` does **not** work, it makes git try to
  run the empty string as a command and fail.
- No pager (``core.pager=cat``), no interactive editor invocation
  (``GIT_EDITOR=true`` — a no-op editor that always "succeeds" immediately;
  every commit in this module always passes ``-m``, so it's a safety net, not
  load-bearing), no credential prompts (``GIT_TERMINAL_PROMPT=0`` plus a
  ``GIT_ASKPASS`` that always fails rather than hanging or leaking a prompt
  into captured output).
- No network operation is exposed by this module at all (no fetch, pull,
  push, or clone) — the credential-isolation requirement is met by there
  being no code path that could need credentials, not merely by suppressing
  prompts on one that could.
"""

from __future__ import annotations

import dataclasses
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from ocode_sandbox.trust import verify_trust

DEFAULT_TIMEOUT_SECONDS = 30
_REF_NAME_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{4,40}$")


class WorkspaceNotTrustedError(RuntimeError):
    """Same fail-closed contract as every prior bite: no valid trust marker,
    no git process is ever spawned."""


class GitOperationError(RuntimeError):
    def __init__(self, args: List[str], returncode: int, stderr: str, stdout: str = ""):
        # git sends some failure explanations (e.g. "nothing to commit") to
        # stdout, not stderr; fall back to stdout so the message is never
        # silently empty just because git chose the "wrong" stream.
        detail = stderr.strip() or stdout.strip()
        super().__init__(f"git {' '.join(args)} failed ({returncode}): {detail}")
        self.args_list = args
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout


class PathEscapeError(ValueError):
    """Same discipline as Bite 4's file service: a path outside the workspace
    (including through a symlink) is rejected before touching git at all."""


class InvalidRefError(ValueError):
    """A branch/tag/stash ref or commit-ish that doesn't look like one —
    rejected outright rather than passed to git, where a string starting with
    ``-`` could be misread as an option flag."""


_hooks_dir_cache: Optional[str] = None


def _empty_hooks_dir() -> str:
    global _hooks_dir_cache
    if _hooks_dir_cache is None:
        _hooks_dir_cache = tempfile.mkdtemp(prefix="ocode-git-empty-hooks-")
    return _hooks_dir_cache


def _base_env() -> dict:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "false"  # /usr/bin/false-equivalent: always fails, never hangs/prompts
    env["SSH_ASKPASS"] = "false"
    env["GIT_EDITOR"] = "true"
    env["EDITOR"] = "true"
    env["GIT_PAGER"] = "cat"
    return env


def validate_ref(name: str) -> str:
    if not name or not _REF_NAME_RE.match(name) or name.startswith("-"):
        raise InvalidRefError(f"not a valid ref/branch/tag name: {name!r}")
    return name


def validate_sha(sha: str) -> str:
    if not _SHA_RE.match(sha):
        raise InvalidRefError(f"not a valid commit sha: {sha!r}")
    return sha


PROTECTED_DIR_NAME = ".ocode"


def resolve_safe_path(workspace: Path, rel_path: str) -> Path:
    workspace = workspace.resolve()
    if not rel_path or rel_path.startswith("/") or rel_path.startswith("\\"):
        raise PathEscapeError(f"path must be relative and non-empty: {rel_path!r}")
    resolved = (workspace / rel_path).resolve()
    try:
        relative = resolved.relative_to(workspace)
    except ValueError:
        raise PathEscapeError(f"path escapes workspace: {rel_path!r} -> {resolved}") from None
    if relative.parts and relative.parts[0] == PROTECTED_DIR_NAME:
        raise PathEscapeError(f"path targets protected metadata directory: {rel_path!r}")
    return resolved


def _is_protected(path: str) -> bool:
    return path == PROTECTED_DIR_NAME or path.startswith(PROTECTED_DIR_NAME + "/")


def run(
    workspace: Path,
    args: List[str],
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    check: bool = True,
) -> subprocess.CompletedProcess:
    workspace = Path(workspace).resolve()
    if verify_trust(workspace) is None:
        raise WorkspaceNotTrustedError(f"workspace is not trusted (no valid trust marker): {workspace}")

    full_args = [
        "git",
        "-C",
        str(workspace),
        "-c",
        f"core.hooksPath={_empty_hooks_dir()}",
        "-c",
        "core.pager=cat",
        "-c",
        "advice.detachedHead=false",
        *args,
    ]
    try:
        proc = subprocess.run(
            full_args,
            cwd=str(workspace),
            env=_base_env(),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitOperationError(full_args, -1, f"timed out after {timeout}s: {exc}") from exc

    if check and proc.returncode != 0:
        raise GitOperationError(full_args, proc.returncode, proc.stderr, proc.stdout)
    return proc


# -- data shapes --------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class GitStatus:
    staged: List[str]
    unstaged: List[str]
    untracked: List[str]
    conflicted: List[str]


@dataclasses.dataclass(frozen=True)
class Commit:
    sha: str
    author: str
    date: str
    subject: str


@dataclasses.dataclass(frozen=True)
class Branch:
    name: str
    is_current: bool


_CONFLICT_CODES = {"UU", "AA", "DD", "AU", "UA", "UD", "DU"}


def status(workspace: Path) -> GitStatus:
    proc = run(workspace, ["status", "--porcelain=v1"])
    staged: List[str] = []
    unstaged: List[str] = []
    untracked: List[str] = []
    conflicted: List[str] = []

    for line in proc.stdout.splitlines():
        if not line:
            continue
        # porcelain v1 lines are always "XY PATH" with XY exactly 2 chars.
        xy = line[:2]
        path = line[3:]
        if _is_protected(path):
            # OCode's own control-plane metadata (trust marker, evidence,
            # secrets in later bites) is never shown as stageable/committable
            # through this service — same discipline as Bite 4's file service
            # hiding it from the editor's file tree entirely.
            continue
        if xy in _CONFLICT_CODES:
            conflicted.append(path)
        elif xy == "??":
            untracked.append(path)
        else:
            x, y = xy[0], xy[1]
            if x != " " and x != "?":
                staged.append(path)
            if y != " " and y != "?":
                unstaged.append(path)

    return GitStatus(staged=staged, unstaged=unstaged, untracked=untracked, conflicted=conflicted)


def diff(workspace: Path, path: Optional[str] = None, *, staged: bool = False) -> str:
    args = ["diff", "--no-ext-diff", "--no-color"]
    if staged:
        args.append("--cached")
    if path:
        resolve_safe_path(workspace, path)  # raises PathEscapeError if invalid
        args += ["--", path]
    return run(workspace, args).stdout


def stage(workspace: Path, paths: List[str]) -> None:
    for p in paths:
        resolve_safe_path(workspace, p)
    run(workspace, ["add", "--", *paths])


def unstage(workspace: Path, paths: List[str]) -> None:
    for p in paths:
        resolve_safe_path(workspace, p)
    run(workspace, ["restore", "--staged", "--", *paths])


def commit(workspace: Path, message: str) -> str:
    run(workspace, ["commit", "-m", message])
    return run(workspace, ["rev-parse", "HEAD"]).stdout.strip()


_LOG_SEP = "\x1f"
_LOG_RECORD_SEP = "\x1e"


def log(workspace: Path, limit: int = 50) -> List[Commit]:
    fmt = _LOG_SEP.join(["%H", "%an", "%ad", "%s"]) + _LOG_RECORD_SEP
    proc = run(
        workspace,
        ["log", f"-n{int(limit)}", "--date=iso-strict", f"--pretty=format:{fmt}", "--no-color"],
        check=False,
    )
    if proc.returncode != 0:
        return []  # empty repo with no commits yet
    commits = []
    for record in proc.stdout.split(_LOG_RECORD_SEP):
        record = record.strip("\n")
        if not record:
            continue
        sha, author, date, subject = record.split(_LOG_SEP)
        commits.append(Commit(sha=sha, author=author, date=date, subject=subject))
    return commits


def current_branch(workspace: Path) -> str:
    return run(workspace, ["branch", "--show-current"]).stdout.strip()


def branches(workspace: Path) -> List[Branch]:
    current = current_branch(workspace)
    proc = run(workspace, ["for-each-ref", "--format=%(refname:short)", "refs/heads/"])
    names = [n for n in proc.stdout.splitlines() if n]
    return [Branch(name=n, is_current=(n == current)) for n in names]


def create_branch(workspace: Path, name: str) -> None:
    validate_ref(name)
    run(workspace, ["branch", "--", name])


def switch_branch(workspace: Path, name: str) -> None:
    validate_ref(name)
    run(workspace, ["switch", "--", name])


def delete_branch(workspace: Path, name: str) -> None:
    validate_ref(name)
    if name == current_branch(workspace):
        raise GitOperationError(["branch", "-d", name], 1, "refusing to delete the current branch")
    run(workspace, ["branch", "-d", "--", name])


def tags(workspace: Path) -> List[str]:
    proc = run(workspace, ["tag", "--list"])
    return [t for t in proc.stdout.splitlines() if t]


def create_tag(workspace: Path, name: str) -> None:
    validate_ref(name)
    run(workspace, ["tag", "--", name])


def stash_save(workspace: Path, message: Optional[str] = None) -> None:
    args = ["stash", "push"]
    if message:
        args += ["-m", message]
    run(workspace, args)


def stash_list(workspace: Path) -> List[str]:
    proc = run(workspace, ["stash", "list", "--no-color"])
    return [l for l in proc.stdout.splitlines() if l]


def stash_pop(workspace: Path, index: int = 0) -> None:
    run(workspace, ["stash", "pop", f"stash@{{{int(index)}}}"])


def stash_drop(workspace: Path, index: int = 0) -> None:
    run(workspace, ["stash", "drop", f"stash@{{{int(index)}}}"])


def restore(workspace: Path, path: str) -> None:
    resolve_safe_path(workspace, path)
    run(workspace, ["restore", "--", path])


def cherry_pick(workspace: Path, sha: str) -> None:
    validate_sha(sha)
    run(workspace, ["cherry-pick", sha])


def cherry_pick_abort(workspace: Path) -> None:
    run(workspace, ["cherry-pick", "--abort"], check=False)


def rebase(workspace: Path, onto: str) -> None:
    validate_ref(onto)
    run(workspace, ["rebase", onto])


def rebase_abort(workspace: Path) -> None:
    run(workspace, ["rebase", "--abort"], check=False)


def merge(workspace: Path, branch: str) -> None:
    validate_ref(branch)
    run(workspace, ["merge", "--no-edit", branch])


def merge_abort(workspace: Path) -> None:
    run(workspace, ["merge", "--abort"], check=False)


def conflicted_files(workspace: Path) -> List[str]:
    return status(workspace).conflicted


def resolve(workspace: Path, path: str, strategy: str) -> None:
    resolve_safe_path(workspace, path)
    if strategy == "ours":
        run(workspace, ["checkout", "--ours", "--", path])
    elif strategy == "theirs":
        run(workspace, ["checkout", "--theirs", "--", path])
    elif strategy != "resolved":
        raise ValueError(f"unknown resolve strategy: {strategy!r}")
    run(workspace, ["add", "--", path])
