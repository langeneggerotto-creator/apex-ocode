"""Seccomp deny-list policy: defense-in-depth blocking of dangerous syscalls.

This is intentionally an allow-by-default / deny-list filter, not a strict
allow-list: the primary isolation boundary for this bite is namespaces + cleared
capability bounding set + read-only filesystem + network deny; seccomp adds a second,
independent layer against specific dangerous syscalls that capability dropping alone
does not fully cover on every kernel (for example, some info-leak or timing
syscalls). A strict per-language allow-list is out of scope for this bite.

Fail closed: if libseccomp / pyseccomp is unavailable, or filter load fails, the
sandbox must refuse to run rather than silently execute unconfined.
"""

from __future__ import annotations

from typing import List, NoReturn, Tuple

DENIED_SYSCALLS: Tuple[str, ...] = (
    "ptrace",
    "mount",
    "umount2",
    "umount",
    "pivot_root",
    "reboot",
    "kexec_load",
    "kexec_file_load",
    "init_module",
    "finit_module",
    "delete_module",
    "acct",
    "swapon",
    "swapoff",
    "quotactl",
    "add_key",
    "request_key",
    "keyctl",
    "bpf",
    "perf_event_open",
    "unshare",
    "setns",
    "syslog",
    "open_by_handle_at",
    "process_vm_readv",
    "process_vm_writev",
    "kcmp",
)


class SeccompUnavailableError(RuntimeError):
    """Raised when a seccomp deny-list filter cannot be built and loaded."""


def seccomp_available() -> bool:
    try:
        import pyseccomp  # noqa: F401
    except (ImportError, OSError):
        return False
    return True


def build_filter():
    """Build (but do not load) the deny-list filter. Raises SeccompUnavailableError
    if pyseccomp/libseccomp cannot be imported."""
    try:
        import pyseccomp as seccomp
    except (ImportError, OSError) as exc:
        raise SeccompUnavailableError(f"pyseccomp/libseccomp unavailable: {exc}") from exc

    filt = seccomp.SyscallFilter(defaction=seccomp.ALLOW)
    applied: List[str] = []
    for name in DENIED_SYSCALLS:
        try:
            filt.add_rule(seccomp.ERRNO(1), name)  # EPERM
            applied.append(name)
        except (OSError, RuntimeError):
            # Syscall not defined on this architecture/kernel; skip individually
            # rather than aborting the whole filter.
            continue

    if not applied:
        raise SeccompUnavailableError("no denied syscalls could be resolved on this host")

    return filt, applied


def apply_and_exec(argv: List[str]) -> NoReturn:
    """Load the deny-list filter in the current process, then execvp into argv.
    Must be called after all other privilege-dropping steps (capabilities, uid) and
    immediately before exec, since the filter applies to this process and everything
    it execs from here on."""
    import os

    filt, _applied = build_filter()
    filt.load()
    os.execvp(argv[0], argv)
