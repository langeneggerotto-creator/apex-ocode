from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

from dreammusicforge.music.errors import AudioInspectionError
from dreammusicforge.music.wav_inspector import inspect_wav


def _write_wav(path: Path, seconds: float, sample_rate: int = 44100, channels: int = 2, sample_width: int = 2) -> None:
    frame_count = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_width)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00" * (frame_count * channels * sample_width))


def _write_empty_wav(path: Path, sample_rate: int = 44100, channels: int = 2, sample_width: int = 2) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_width)
        handle.setframerate(sample_rate)
        handle.writeframes(b"")


class InspectWavTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_reads_duration_sample_rate_channels(self):
        path = self.dir / "song.wav"
        _write_wav(path, seconds=2.0, sample_rate=44100, channels=2)
        metadata = inspect_wav(path)
        self.assertAlmostEqual(metadata.duration_seconds, 2.0, places=3)
        self.assertEqual(metadata.sample_rate, 44100)
        self.assertEqual(metadata.channels, 2)
        self.assertEqual(metadata.sample_width_bytes, 2)

    def test_mono_file(self):
        path = self.dir / "mono.wav"
        _write_wav(path, seconds=1.0, channels=1)
        metadata = inspect_wav(path)
        self.assertEqual(metadata.channels, 1)


class InspectWavFailureTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_file_raises(self):
        with self.assertRaises(AudioInspectionError):
            inspect_wav(self.dir / "does-not-exist.wav")

    def test_not_a_wav_file_raises(self):
        path = self.dir / "not-a-wav.wav"
        path.write_bytes(b"this is not a wav file")
        with self.assertRaises(AudioInspectionError):
            inspect_wav(path)

    def test_zero_frames_raises(self):
        path = self.dir / "empty.wav"
        _write_empty_wav(path)
        with self.assertRaises(AudioInspectionError):
            inspect_wav(path)

    def test_os_error_from_wave_open_becomes_audio_inspection_error(self):
        """A file that exists (passes is_file()) but can't actually be
        opened -- permission denied, a disk I/O error, a file replaced
        mid-read -- must still surface as the typed AudioInspectionError,
        not a bare OSError leaking past this module's boundary."""
        path = self.dir / "song.wav"
        _write_wav(path, seconds=1.0)
        with mock.patch("wave.open", side_effect=OSError("permission denied")):
            with self.assertRaises(AudioInspectionError):
                inspect_wav(path)


if __name__ == "__main__":
    unittest.main()
