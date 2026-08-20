"""RunwayClient: a real, functioning HTTP client for Runway's actual
video-generation API -- stdlib `urllib.request` only, no new
dependency, same "allowlisted, argv/request-construction is
self-contained" discipline every ffmpeg wrapper in this repository
applies to subprocess calls.

**This code has not been run against Runway's live API in this
session** -- no `RUNWAY_API_KEY` was available, and making a real,
billed API call without the user's explicit credential and
authorization would violate this repository's rule against claiming an
integration that wasn't actually exercised (spec section 22). What
*is* real: the request/response shapes below are grounded in Runway's
public API documentation (base URL, endpoint paths, header names, the
async task-submission-then-poll pattern, and the PENDING/RUNNING/
SUCCEEDED/FAILED status vocabulary), and the request-building/response-
parsing logic is unit-tested against mocked HTTP responses shaped like
Runway's documented ones (see tests/providers/runway/test_client.py).
Whether the live endpoint accepts these exact requests unchanged can
only be confirmed by actually running this against a real API key --
that verification is this module's one honest, disclosed gap.

Usage once a real key is available:

    from dreammusicforge.providers.runway.client import RunwayClient
    client = RunwayClient()  # reads RUNWAY_API_KEY from the environment
    task_id = client.submit_task(package)
    result = client.wait_for_completion(task_id)
    output_url = result["output"][0]
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from .errors import RunwayClientError
from .models import RunwayPackage

RUNWAY_API_BASE_URL = "https://api.dev.runwayml.com/v1"
RUNWAY_API_VERSION = "2024-11-06"
TERMINAL_TASK_STATUSES = ("SUCCEEDED", "FAILED")

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_POLL_TIMEOUT_SECONDS = 600.0


def _api_key_from_env() -> str:
    api_key = os.environ.get("RUNWAY_API_KEY")
    if not api_key:
        raise RunwayClientError(["RUNWAY_API_KEY is not set -- a real Runway API key is required to call the live API"])
    return api_key


class RunwayClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = RUNWAY_API_BASE_URL,
        api_version: str = RUNWAY_API_VERSION,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.api_key = api_key or _api_key_from_env()
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Runway-Version": self.api_version,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RunwayClientError([f"{method} {path} failed with HTTP {exc.code}: {detail}"]) from exc
        except urllib.error.URLError as exc:
            raise RunwayClientError([f"{method} {path} failed: {exc.reason}"]) from exc

    def submit_task(self, package: RunwayPackage) -> str:
        """POSTs the package to Runway's real image_to_video or
        text_to_video endpoint (chosen by package.mode) and returns
        the task id Runway assigns for polling."""
        endpoint = f"/{package.mode}"
        body: dict[str, Any] = {
            "model": package.model,
            "promptText": package.prompt_text,
            "ratio": package.ratio,
            "duration": package.duration_seconds,
        }
        if package.mode == "image_to_video":
            if not package.prompt_image:
                raise RunwayClientError([f"package {package.id!r} has mode 'image_to_video' but no prompt_image"])
            body["promptImage"] = package.prompt_image
        if package.seed is not None:
            body["seed"] = package.seed

        response = self._request("POST", endpoint, body)
        task_id = response.get("id")
        if not task_id:
            raise RunwayClientError([f"Runway response for package {package.id!r} did not include a task id: {response}"])
        return task_id

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """GETs the real task status -- id, status
        (PENDING/RUNNING/SUCCEEDED/FAILED), and, once SUCCEEDED, an
        `output` list of result URLs."""
        return self._request("GET", f"/tasks/{task_id}")

    def wait_for_completion(
        self,
        task_id: str,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        timeout_seconds: float = DEFAULT_POLL_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        """Polls get_task_status() until it reaches a terminal status
        (SUCCEEDED/FAILED) or timeout_seconds elapses. Runway's own
        docs ask callers not to expect updates more often than every
        5 seconds for a given task -- poll_interval_seconds defaults
        to that."""
        elapsed = 0.0
        while True:
            status = self.get_task_status(task_id)
            if status.get("status") in TERMINAL_TASK_STATUSES:
                if status.get("status") == "FAILED":
                    raise RunwayClientError([f"task {task_id!r} failed: {status.get('failure', status)}"])
                return status
            if elapsed >= timeout_seconds:
                raise RunwayClientError([f"task {task_id!r} did not complete within {timeout_seconds}s (last status: {status.get('status')!r})"])
            time.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds

    def download_output(self, output_url: str, destination: str, timeout_seconds: float | None = None) -> str:
        """Downloads a completed task's output file to a real local
        path via a plain GET -- Runway's task outputs are themselves
        plain HTTPS URLs, not authenticated API responses."""
        try:
            urllib.request.urlretrieve(output_url, destination)
        except urllib.error.URLError as exc:
            raise RunwayClientError([f"failed to download {output_url!r}: {exc.reason}"]) from exc
        return destination
