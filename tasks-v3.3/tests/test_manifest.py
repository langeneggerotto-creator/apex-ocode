"""Unit tests for manifest parsing — pure logic, no sandbox prerequisites."""

from __future__ import annotations

import pytest

from ocode_tasks.manifest import ManifestError, parse


def test_valid_manifest_parses() -> None:
    manifest = parse(
        '{"tasks": {"test": {"type": "test", "command": ["pytest", "-q"], "timeout_seconds": 120}}}'
    )
    spec = manifest.get("test")
    assert spec.type == "test"
    assert spec.command == ["pytest", "-q"]
    assert spec.timeout_seconds == 120


def test_default_timeout_applied() -> None:
    manifest = parse('{"tasks": {"lint": {"type": "lint", "command": ["ruff", "check"]}}}')
    assert manifest.get("lint").timeout_seconds == 600


def test_unknown_task_raises_keyerror_like() -> None:
    manifest = parse('{"tasks": {}}')
    with pytest.raises(ManifestError):
        manifest.get("does-not-exist")


def test_invalid_json_fails_closed() -> None:
    with pytest.raises(ManifestError):
        parse("{not valid json")


def test_missing_tasks_key_fails_closed() -> None:
    with pytest.raises(ManifestError):
        parse("{}")


def test_unknown_task_type_fails_closed() -> None:
    with pytest.raises(ManifestError):
        parse('{"tasks": {"x": {"type": "not-a-real-type", "command": ["echo", "hi"]}}}')


def test_missing_command_fails_closed() -> None:
    with pytest.raises(ManifestError):
        parse('{"tasks": {"x": {"type": "run"}}}')


def test_empty_command_fails_closed() -> None:
    with pytest.raises(ManifestError):
        parse('{"tasks": {"x": {"type": "run", "command": []}}}')


def test_non_string_command_element_fails_closed() -> None:
    with pytest.raises(ManifestError):
        parse('{"tasks": {"x": {"type": "run", "command": ["echo", 5]}}}')


def test_non_positive_timeout_fails_closed() -> None:
    with pytest.raises(ManifestError):
        parse('{"tasks": {"x": {"type": "run", "command": ["echo"], "timeout_seconds": 0}}}')


def test_resource_limit_overrides_parsed() -> None:
    manifest = parse(
        '{"tasks": {"build": {"type": "build", "command": ["make"], '
        '"memory_bytes": 1048576, "pids_max": 16, "cpu_quota_percent": 50}}}'
    )
    spec = manifest.get("build")
    assert spec.memory_bytes == 1048576
    assert spec.pids_max == 16
    assert spec.cpu_quota_percent == 50
