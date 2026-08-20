"""RunwayClient: a thin, typed wrapper around the official `runwayml`
Python SDK (`pip install runwayml`) -- verified installable and
importable in this environment (`pip install --dry-run runwayml`
resolved and downloaded real wheels from PyPI), and its real resource
methods (`image_to_video.create()`, `text_to_video.create()`,
`tasks.retrieve()`, `uploads.create_ephemeral()`) were introspected
directly from the installed package to ground this file -- a stronger
form of verification than the first version of this package used
(web-search summaries of docs pages this environment's egress proxy
blocks direct access to).

**This code has still not been run against Runway's live API in this
session** -- no `RUNWAYML_API_SECRET` was available, and making a
real, billed API call without the user's explicit credential and
authorization would violate this repository's rule against claiming an
integration that wasn't actually exercised (spec section 22). What
changed since the first version: request/response shapes are now
grounded in the actual installed SDK's type signatures and Pydantic
models, not secondhand summaries -- so the remaining gap is narrower
and more honestly stated: the SDK itself is real and tested by its own
maintainers against the live API; what's untested *here* is only
whether this thin wrapper calls it correctly, which is covered by
tests/providers/runway/test_client.py mocking the SDK's resource
methods (not the raw HTTP layer, since the SDK now owns that).

`runwayml` is an optional dependency (see pyproject.toml's
`[project.optional-dependencies]` -- `pip install dreammusicforge[runway]`
or just `pip install runwayml`), not a hard one: everything else in
this repository stays dependency-free-until-necessary, and most of
this codebase's tests must keep running without it installed.
RunwayClient raises a clear, typed error if it's missing rather than
an opaque ImportError.

Usage once a real key is available:

    from dreammusicforge.providers.runway.client import RunwayClient
    client = RunwayClient()  # reads RUNWAYML_API_SECRET from the environment
    task_id = client.submit_task(package)
    result = client.wait_for_completion(task_id)
    local_path = client.download_output(result["output"][0], "shot017.mp4")
    # then, same as any other candidate in this pipeline:
    #   core.hashing.hash_file(local_path) + verification.inspect_media(local_path)
"""
from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .errors import RunwayClientError
from .models import RunwayPackage

try:
    import runwayml
except ImportError:  # pragma: no cover -- exercised by test_client.py's own import guard test
    runwayml = None

TERMINAL_TASK_STATUSES = ("SUCCEEDED", "FAILED", "CANCELLED")
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_POLL_TIMEOUT_SECONDS = 600.0


def _require_sdk() -> None:
    if runwayml is None:
        raise RunwayClientError([
            "the 'runwayml' package is not installed -- run `pip install runwayml` "
            "(or `pip install dreammusicforge[runway]`) to use RunwayClient"
        ])


class RunwayClient:
    def __init__(self, api_key: str | None = None):
        _require_sdk()
        try:
            self._client = runwayml.RunwayML(api_key=api_key)
        except runwayml.RunwayMLError as exc:
            raise RunwayClientError([str(exc)]) from exc

    def upload_asset(self, file_path: Path) -> str:
        """Uploads a local file through Runway's real ephemeral-uploads
        API and returns the `runway://`-style URI a generation request
        can reference -- Runway's API cannot consume an arbitrary local
        filesystem path directly. Ephemeral uploads expire (Runway's
        docs say within 24 hours); the returned URI is a temporary
        provider binding, not a permanent asset identity -- a caller
        should keep tracking the original file/its own asset id as the
        canonical reference, the same way this package's
        RunwayPackage.reference_manifest is separate from prompt_image."""
        with open(file_path, "rb") as handle:
            try:
                response = self._client.uploads.create_ephemeral(file=handle)
            except runwayml.APIError as exc:
                raise RunwayClientError([f"upload of {file_path} failed: {exc}"]) from exc
        return response.uri

    def submit_task(self, package: RunwayPackage) -> str:
        """Calls the real image_to_video.create()/text_to_video.create()
        SDK method matching package.mode and returns the task id Runway
        assigns for polling."""
        resource = getattr(self._client, package.mode, None)
        if resource is None:
            raise RunwayClientError([f"unsupported mode {package.mode!r} -- no matching resource on the runwayml client"])
        if package.mode == "image_to_video" and not package.prompt_image:
            raise RunwayClientError([f"package {package.id!r} has mode 'image_to_video' but no prompt_image"])

        kwargs: dict[str, Any] = {
            "model": package.model,
            "ratio": package.ratio,
            "duration": int(round(package.duration_seconds)),
        }
        if package.prompt_text:
            kwargs["prompt_text"] = package.prompt_text
        if package.prompt_image:
            kwargs["prompt_image"] = package.prompt_image
        if package.negative_prompt:
            kwargs["negative_prompt"] = package.negative_prompt
        if package.seed is not None:
            kwargs["seed"] = package.seed
        if package.audio:
            kwargs["audio"] = True

        try:
            response = resource.create(**kwargs)
        except runwayml.APIError as exc:
            raise RunwayClientError([f"submit_task failed for package {package.id!r}: {exc}"]) from exc
        return response.id

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Returns the real task status as a plain dict -- id, status
        (PENDING/THROTTLED/RUNNING/SUCCEEDED/FAILED/CANCELLED), and,
        once SUCCEEDED, an `output` list of result URLs that Runway's
        own SDK docstring says expire within 24-48 hours."""
        try:
            response = self._client.tasks.retrieve(task_id)
        except runwayml.APIError as exc:
            raise RunwayClientError([f"get_task_status failed for {task_id!r}: {exc}"]) from exc
        return response.model_dump(by_alias=False)

    def wait_for_completion(
        self,
        task_id: str,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        timeout_seconds: float = DEFAULT_POLL_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        """Polls get_task_status() until it reaches a terminal status
        (SUCCEEDED/FAILED/CANCELLED) or timeout_seconds elapses.
        PENDING/THROTTLED/RUNNING are all treated as "keep polling" --
        THROTTLED means Runway accepted the task but is queueing it
        under the account's concurrency limits, not that it failed."""
        elapsed = 0.0
        while True:
            status = self.get_task_status(task_id)
            state = status.get("status")
            if state in TERMINAL_TASK_STATUSES:
                if state != "SUCCEEDED":
                    raise RunwayClientError([f"task {task_id!r} ended with status {state!r}: {status.get('failure', status)}"])
                return status
            if elapsed >= timeout_seconds:
                raise RunwayClientError([f"task {task_id!r} did not complete within {timeout_seconds}s (last status: {state!r})"])
            time.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds

    def download_output(self, output_url: str, destination: str) -> str:
        """Downloads a completed task's output to a real local path via
        a plain GET -- Runway's task outputs are themselves plain HTTPS
        URLs, not authenticated SDK calls, and Runway explicitly
        expects callers to download and store them in their own
        storage rather than treat the temporary URL as permanent.
        Pairing this with core.hashing.hash_file() and
        verification.inspect_media() (both already exist in this
        repository) is the intended next step -- not duplicated here."""
        try:
            urllib.request.urlretrieve(output_url, destination)
        except urllib.error.URLError as exc:
            raise RunwayClientError([f"failed to download {output_url!r}: {exc.reason}"]) from exc
        return destination
