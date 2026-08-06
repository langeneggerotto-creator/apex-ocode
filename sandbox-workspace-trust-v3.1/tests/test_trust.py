from pathlib import Path

import pytest

from ocode_sandbox.trust import establish_trust, revoke_trust, verify_trust


def test_untrusted_workspace_has_no_record(tmp_path: Path) -> None:
    assert verify_trust(tmp_path) is None


def test_establish_then_verify_round_trip(tmp_path: Path) -> None:
    record = establish_trust(tmp_path, actor="alice")
    verified = verify_trust(tmp_path)
    assert verified is not None
    assert verified.actor == "alice"
    assert verified.trusted is True
    assert verified.workspace == str(tmp_path.resolve())
    assert verified.content_hash == record.content_hash


def test_establish_requires_nonempty_actor(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        establish_trust(tmp_path, actor="")


def test_establish_requires_existing_workspace(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        establish_trust(tmp_path / "does-not-exist", actor="alice")


def test_tampered_trust_marker_fails_closed(tmp_path: Path) -> None:
    establish_trust(tmp_path, actor="alice")
    trust_path = tmp_path / ".ocode" / "trust.json"
    text = trust_path.read_text()
    tampered = text.replace('"actor": "alice"', '"actor": "mallory"')
    trust_path.write_text(tampered)
    assert verify_trust(tmp_path) is None


def test_wrong_schema_version_fails_closed(tmp_path: Path) -> None:
    establish_trust(tmp_path, actor="alice")
    trust_path = tmp_path / ".ocode" / "trust.json"
    text = trust_path.read_text().replace("ocode.workspace-trust.v1", "ocode.workspace-trust.v999")
    trust_path.write_text(text)
    assert verify_trust(tmp_path) is None


def test_trusted_false_fails_closed(tmp_path: Path) -> None:
    establish_trust(tmp_path, actor="alice")
    trust_path = tmp_path / ".ocode" / "trust.json"
    text = trust_path.read_text().replace('"trusted": true', '"trusted": false')
    trust_path.write_text(text)
    assert verify_trust(tmp_path) is None


def test_malformed_json_fails_closed(tmp_path: Path) -> None:
    trust_dir = tmp_path / ".ocode"
    trust_dir.mkdir()
    (trust_dir / "trust.json").write_text("{not valid json")
    assert verify_trust(tmp_path) is None


def test_revoke_removes_marker(tmp_path: Path) -> None:
    establish_trust(tmp_path, actor="alice")
    assert verify_trust(tmp_path) is not None
    assert revoke_trust(tmp_path) is True
    assert verify_trust(tmp_path) is None
    assert revoke_trust(tmp_path) is False
