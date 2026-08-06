"""OCode Bite 3 — declarative tasks, structured job states, and a concurrency-
limited job manager (local mode), built on Bite 1's unmodified sandbox primitives."""

from .client import JobClient, JobServiceUnavailableError
from .job import Job, JobState
from .manager import JobManager
from .manifest import ManifestError, TaskManifest, TaskSpec, load as load_manifest

__all__ = [
    "JobClient",
    "JobServiceUnavailableError",
    "Job",
    "JobState",
    "JobManager",
    "ManifestError",
    "TaskManifest",
    "TaskSpec",
    "load_manifest",
]
