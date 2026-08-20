"""Tests RunwayClient's thin wrapper logic against a mocked `runwayml`
SDK client -- no real network call, no real API key needed, and no
need to fake HTTP responses by hand since the real SDK's own response
types are used directly. This does NOT prove Runway's live API accepts
these exact requests; see client.py's module docstring for that
disclosed gap -- what it proves is that this wrapper calls the real,
installed SDK correctly."""
from __future__ import annotations

import unittest
from unittest import mock

import runwayml

from dreammusicforge.providers.runway.client import RunwayClient
from dreammusicforge.providers.runway.errors import RunwayClientError
from dreammusicforge.providers.runway.models import RunwayPackage


def _package(mode="image_to_video", prompt_image="https://example.com/ref.png", negative_prompt="blurry", seed=None, audio=False):
    return RunwayPackage(
        id="RUNWAY-deadbeef", render_task_id="RENDER-deadbeef", shot_id="SHOT-deadbeef",
        mode=mode, model="gen4_turbo", prompt_text="animate this", duration_seconds=6.0,
        ratio="1280:720", prompt_image=prompt_image, negative_prompt=negative_prompt, seed=seed, audio=audio,
    )


class RunwayClientConstructionTests(unittest.TestCase):
    @mock.patch("runwayml.RunwayML")
    def test_api_key_is_passed_through_to_the_sdk(self, mock_sdk_cls):
        RunwayClient(api_key="explicit-key")
        mock_sdk_cls.assert_called_once_with(api_key="explicit-key")

    @mock.patch("runwayml.RunwayML", side_effect=runwayml.RunwayMLError("RUNWAYML_API_SECRET not set"))
    def test_sdk_construction_error_is_wrapped(self, mock_sdk_cls):
        with self.assertRaises(RunwayClientError):
            RunwayClient()


class RunwayClientSubmitTaskTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("runwayml.RunwayML")
        self.addCleanup(patcher.stop)
        self.mock_sdk_cls = patcher.start()
        self.mock_sdk = self.mock_sdk_cls.return_value
        self.client = RunwayClient(api_key="test-key")

    def test_submit_task_calls_image_to_video_create_with_the_right_kwargs(self):
        self.mock_sdk.image_to_video.create.return_value = mock.MagicMock(id="task-123")
        package = _package(mode="image_to_video", seed=42, audio=True)

        task_id = self.client.submit_task(package)

        self.assertEqual(task_id, "task-123")
        self.mock_sdk.image_to_video.create.assert_called_once_with(
            model="gen4_turbo", ratio="1280:720", duration=6,
            prompt_text="animate this", prompt_image="https://example.com/ref.png",
            negative_prompt="blurry", seed=42, audio=True,
        )

    def test_submit_task_calls_text_to_video_create_and_omits_prompt_image(self):
        self.mock_sdk.text_to_video.create.return_value = mock.MagicMock(id="task-456")
        package = _package(mode="text_to_video", prompt_image=None)

        self.client.submit_task(package)

        called_kwargs = self.mock_sdk.text_to_video.create.call_args.kwargs
        self.assertNotIn("prompt_image", called_kwargs)

    def test_image_to_video_without_prompt_image_raises_before_calling_the_sdk(self):
        package = _package(mode="image_to_video", prompt_image=None)
        with self.assertRaises(RunwayClientError):
            self.client.submit_task(package)
        self.mock_sdk.image_to_video.create.assert_not_called()

    def test_api_error_from_the_sdk_is_wrapped(self):
        self.mock_sdk.image_to_video.create.side_effect = runwayml.APIError(
            "bad request", request=mock.MagicMock(), body=None,
        )
        with self.assertRaises(RunwayClientError):
            self.client.submit_task(_package())


class RunwayClientPollingTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("runwayml.RunwayML")
        self.addCleanup(patcher.stop)
        self.mock_sdk_cls = patcher.start()
        self.mock_sdk = self.mock_sdk_cls.return_value
        self.client = RunwayClient(api_key="test-key")

    def test_get_task_status_returns_a_plain_dict(self):
        self.mock_sdk.tasks.retrieve.return_value = mock.MagicMock(model_dump=lambda by_alias=False: {"id": "task-123", "status": "RUNNING"})
        status = self.client.get_task_status("task-123")
        self.assertEqual(status["status"], "RUNNING")
        self.mock_sdk.tasks.retrieve.assert_called_once_with("task-123")

    @mock.patch("time.sleep", return_value=None)
    def test_wait_for_completion_polls_through_pending_and_throttled_to_succeeded(self, mock_sleep):
        responses = [
            {"id": "task-123", "status": "PENDING"},
            {"id": "task-123", "status": "THROTTLED"},
            {"id": "task-123", "status": "RUNNING"},
            {"id": "task-123", "status": "SUCCEEDED", "output": ["https://example.com/out.mp4"]},
        ]
        self.mock_sdk.tasks.retrieve.side_effect = [
            mock.MagicMock(model_dump=lambda by_alias=False, r=r: r) for r in responses
        ]
        result = self.client.wait_for_completion("task-123", poll_interval_seconds=0.01, timeout_seconds=10.0)
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["output"], ["https://example.com/out.mp4"])
        self.assertEqual(self.mock_sdk.tasks.retrieve.call_count, 4)

    @mock.patch("time.sleep", return_value=None)
    def test_wait_for_completion_raises_on_failed_status(self, mock_sleep):
        self.mock_sdk.tasks.retrieve.return_value = mock.MagicMock(
            model_dump=lambda by_alias=False: {"id": "task-123", "status": "FAILED", "failure": "content moderation"}
        )
        with self.assertRaises(RunwayClientError):
            self.client.wait_for_completion("task-123", poll_interval_seconds=0.01)

    @mock.patch("time.sleep", return_value=None)
    def test_wait_for_completion_raises_on_cancelled_status(self, mock_sleep):
        self.mock_sdk.tasks.retrieve.return_value = mock.MagicMock(
            model_dump=lambda by_alias=False: {"id": "task-123", "status": "CANCELLED"}
        )
        with self.assertRaises(RunwayClientError):
            self.client.wait_for_completion("task-123", poll_interval_seconds=0.01)

    @mock.patch("time.sleep", return_value=None)
    def test_wait_for_completion_raises_on_timeout(self, mock_sleep):
        self.mock_sdk.tasks.retrieve.return_value = mock.MagicMock(
            model_dump=lambda by_alias=False: {"id": "task-123", "status": "RUNNING"}
        )
        with self.assertRaises(RunwayClientError):
            self.client.wait_for_completion("task-123", poll_interval_seconds=1.0, timeout_seconds=2.0)


class RunwayClientUploadTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("runwayml.RunwayML")
        self.addCleanup(patcher.stop)
        self.mock_sdk_cls = patcher.start()
        self.mock_sdk = self.mock_sdk_cls.return_value
        self.client = RunwayClient(api_key="test-key")

    def test_upload_asset_returns_the_real_uri(self):
        import tempfile
        from pathlib import Path

        self.mock_sdk.uploads.create_ephemeral.return_value = mock.MagicMock(uri="runway://uploaded-asset-123")
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "ref.png"
            file_path.write_bytes(b"fake-image-bytes")
            uri = self.client.upload_asset(file_path)
        self.assertEqual(uri, "runway://uploaded-asset-123")


if __name__ == "__main__":
    unittest.main()
