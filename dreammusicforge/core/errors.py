"""Deterministic, typed error hierarchy for the DreamMusicForge Film Compiler
kernel. Every error a caller can reasonably need to catch and handle
programmatically has its own type -- callers should never need to inspect a
message string to know what went wrong. Fail closed: nothing in core/ or
storage/ raises a bare Exception or swallows an error silently."""
from __future__ import annotations


class DMFError(Exception):
    """Base class for every error raised by the DreamMusicForge kernel."""


class ProjectValidationError(DMFError):
    """Raised when a project fails schema or semantic validation. Carries
    every error found, not just the first, so a caller can report all of
    them at once instead of fixing issues one round-trip at a time."""

    def __init__(self, errors: list[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors) if self.errors else "project validation failed")


class ProjectNotFoundError(DMFError):
    """Raised when loading a project id that does not exist in the
    repository."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(f"no project found with id {project_id!r}")


class ProjectAlreadyExistsError(DMFError):
    """Raised when creating a project whose id is already in the
    repository -- create() never silently overwrites; use save() to
    update an existing project."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(f"project {project_id!r} already exists -- use save() to update it")


class InvalidProjectIdError(DMFError):
    """Raised when a project id does not match the required DMF-PROJECT-*
    format."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(f"{project_id!r} is not a valid project id (expected DMF-PROJECT-<hex>)")


class PathConfinementError(DMFError):
    """Raised when a path resolves outside its required workspace root --
    covers both literal `..` traversal and symlink escapes, since both are
    named explicitly in the spec's security requirements."""

    def __init__(self, requested: str, root: str):
        self.requested = requested
        self.root = root
        super().__init__(f"path {requested!r} escapes workspace root {root!r}")
