"""Tests RunwayClient's request-building and response-parsing logic
against mocked HTTP responses shaped like Runway's documented ones --
no real network call, no real API key needed. This does NOT prove the
live endpoint behaves this way; see client.py's module docstring for
that disclosed gap."""
from __future__ import annotations

import io
import json
import unittest
from unittest import mock

from dreammusicforge.providers.runway.client import RunwayClient
from dreammusicforge.providers.runway.errors import RunwayClientError
from dreammusicforge.providers.runway.models import RunwayPackage


def _package(mode="image_to_video", prompt_image="https://example.com/ref.png", seed=None):
    return RunwayPackage(
        id="RUNWAY-deadbeef", render_task_id="RENDER-deadbeef", shot_id="SHOT-deadbeef",
        mode=mode, model="gen4_turbo", prompt_text="animate this", duration_seconds=5.0,
        ratio="1280:720", prompt_image=prompt_image, seed=seed,
    )


def _mock_response(payload: dict, status: int = 200):
    body = json.dumps(payload).encode("utf-8")
    response = mock.MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class RunwayClientApiKeyTests(unittest.TestCase):
    def test_missing_api_key_raises(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RunwayClientError):
                RunwayClient()

    def test_explicit_api_key_is_used_over_environment(self):
        client = RunwayClient(api_key="explicit-key")
        self.assertEqual(client.api_key, "explicit-key")
        self.assertIn("Bearer explicit-key", client._headers()["Authorization"])


class RunwayClientSubmitTaskTests(unittest.TestCase):
    def setUp(self):
        self.client = RunwayClient(api_key="test-key")

    @mock.patch("urllib.request.urlopen")
    def test_submit_task_posts_to_the_mode_specific_endpoint(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"id": "task-123"})
        package = _package(mode="image_to_video")

        task_id = self.client.submit_task(package)

        self.assertEqual(task_id, "task-123")
        request = mock_urlopen.call_args[0][0]
        self.assertEqual(request.full_url, "https://api.dev.runwayml.com/v1/image_to_video")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(request.get_header("X-runway-version"), "2024-11-06")
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["promptImage"], "https://example.com/ref.png")
        self.assertEqual(body["model"], "gen4_turbo")
        self.assertEqual(body["duration"], 5.0)

    @mock.patch("urllib.request.urlopen")
    def test_submit_task_text_to_video_omits_prompt_image(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"id": "task-456"})
        package = _package(mode="text_to_video", prompt_image=None)

        self.client.submit_task(package)

        request = mock_urlopen.call_args[0][0]
        self.assertEqual(request.full_url, "https://api.dev.runwayml.com/v1/text_to_video")
        body = json.loads(request.data.decode("utf-8"))
        self.assertNotIn("promptImage", body)

    @mock.patch("urllib.request.urlopen")
    def test_missing_task_id_in_response_raises(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"unexpected": "shape"})
        with self.assertRaises(RunwayClientError):
            self.client.submit_task(_package())

    @mock.patch("urllib.request.urlopen")
    def test_image_to_video_without_prompt_image_raises_before_any_request(self, mock_urlopen):
        package = _package(mode="image_to_video", prompt_image=None)
        with self.assertRaises(RunwayClientError):
            self.client.submit_task(package)
        mock_urlopen.assert_not_called()


class RunwayClientPollingTests(unittest.TestCase):
    def setUp(self):
        self.client = RunwayClient(api_key="test-key")

    @mock.patch("urllib.request.urlopen")
    def test_get_task_status_returns_the_real_shape(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"id": "task-123", "status": "RUNNING"})
        status = self.client.get_task_status("task-123")
        self.assertEqual(status["status"], "RUNNING")
        request = mock_urlopen.call_args[0][0]
        self.assertEqual(request.full_url, "https://api.dev.runwayml.com/v1/tasks/task-123")

    @mock.patch("time.sleep", return_value=None)
    @mock.patch("urllib.request.urlopen")
    def test_wait_for_completion_polls_until_succeeded(self, mock_urlopen, mock_sleep):
        mock_urlopen.side_effect = [
            _mock_response({"id": "task-123", "status": "PENDING"}),
            _mock_response({"id": "task-123", "status": "RUNNING"}),
            _mock_response({"id": "task-123", "status": "SUCCEEDED", "output": ["https://example.com/out.mp4"]}),
        ]
        result = self.client.wait_for_completion("task-123", poll_interval_seconds=0.01, timeout_seconds=10.0)
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["output"], ["https://example.com/out.mp4"])
        self.assertEqual(mock_urlopen.call_count, 3)

    @mock.patch("time.sleep", return_value=None)
    @mock.patch("urllib.request.urlopen")
    def test_wait_for_completion_raises_on_failed_status(self, mock_urlopen, mock_sleep):
        mock_urlopen.return_value = _mock_response({"id": "task-123", "status": "FAILED", "failure": "content moderation"})
        with self.assertRaises(RunwayClientError):
            self.client.wait_for_completion("task-123", poll_interval_seconds=0.01)

    @mock.patch("time.sleep", return_value=None)
    @mock.patch("urllib.request.urlopen")
    def test_wait_for_completion_raises_on_timeout(self, mock_urlopen, mock_sleep):
        mock_urlopen.return_value = _mock_response({"id": "task-123", "status": "RUNNING"})
        with self.assertRaises(RunwayClientError):
            self.client.wait_for_completion("task-123", poll_interval_seconds=1.0, timeout_seconds=2.0)


if __name__ == "__main__":
    unittest.main()
