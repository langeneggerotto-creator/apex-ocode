from __future__ import annotations

from dataclasses import dataclass

from .models import ProductionTwin, TwinState


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    state_id: str | None = None


class ProductionTwinValidationError(ValueError):
    def __init__(self, issues: list[ValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(i.message for i in issues))


def _changed_fields(a: TwinState, b: TwinState) -> set[str]:
    changed: set[str] = set()
    if a.performer.identity_id != b.performer.identity_id:
        changed.add("identity")
    if a.performer.costume_id != b.performer.costume_id:
        changed.add("costume")
    if a.performer.hair_id != b.performer.hair_id:
        changed.add("hair")
    if a.world.world_id != b.world.world_id:
        changed.add("world")
    if a.world.geometry_state_id != b.world.geometry_state_id:
        changed.add("world_geometry")
    if a.camera != b.camera:
        changed.add("camera")
    if a.lighting != b.lighting:
        changed.add("lighting")
    if a.music.song_id != b.music.song_id:
        changed.add("master_song")
    return changed


def validate_twin(twin: ProductionTwin) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    if twin.duration_seconds <= 0:
        issues.append(ValidationIssue("INVALID_DURATION", "Twin duration must be positive."))
    if not twin.states:
        issues.append(ValidationIssue("NO_STATES", "Production Twin must contain at least one state."))
        return tuple(issues)

    ordered = sorted(twin.states, key=lambda s: (s.start_seconds, s.end_seconds, s.state_id))
    if tuple(ordered) != twin.states:
        issues.append(ValidationIssue("STATE_ORDER", "States must be stored in canonical time order."))

    if abs(ordered[0].start_seconds) > 1e-9:
        issues.append(ValidationIssue("TIMELINE_START", "Timeline must start at 0.0 seconds.", ordered[0].state_id))

    for s in ordered:
        if s.end_seconds <= s.start_seconds:
            issues.append(ValidationIssue("STATE_DURATION", "State end must be greater than start.", s.state_id))
        if not 0.0 <= s.experience.intensity <= 1.0:
            issues.append(ValidationIssue("EXPERIENCE_RANGE", "Experience intensity must be between 0 and 1.", s.state_id))
        if not 0.0 <= s.music.energy <= 1.0:
            issues.append(ValidationIssue("MUSIC_RANGE", "Music energy must be between 0 and 1.", s.state_id))
        if abs(s.music.time_seconds - s.start_seconds) > 1e-6:
            issues.append(ValidationIssue("MUSIC_TIME", "Music state time must equal state start time.", s.state_id))

    for a, b in zip(ordered, ordered[1:]):
        if abs(a.end_seconds - b.start_seconds) > 1e-6:
            code = "TIMELINE_GAP" if a.end_seconds < b.start_seconds else "TIMELINE_OVERLAP"
            issues.append(ValidationIssue(code, f"States {a.state_id} and {b.state_id} do not meet exactly."))
        changed = _changed_fields(a, b)
        permitted = set(a.allowed_mutations) | set(b.allowed_mutations)
        forbidden = changed - permitted
        for invariant in set(a.invariants) | set(b.invariants):
            if invariant in changed:
                issues.append(ValidationIssue("INVARIANT_VIOLATION", f"Invariant '{invariant}' changed across {a.state_id}->{b.state_id}."))
        if forbidden:
            issues.append(ValidationIssue("UNDECLARED_MUTATION", f"Undeclared mutations across {a.state_id}->{b.state_id}: {sorted(forbidden)}"))

    if abs(ordered[-1].end_seconds - twin.duration_seconds) > 1e-6:
        issues.append(ValidationIssue("TIMELINE_END", "Final state end must equal twin duration.", ordered[-1].state_id))

    transition_pairs = {(t.source_state_id, t.destination_state_id) for t in twin.transitions}
    expected_pairs = {(a.state_id, b.state_id) for a, b in zip(ordered, ordered[1:])}
    missing = expected_pairs - transition_pairs
    if missing:
        issues.append(ValidationIssue("MISSING_TRANSITION", f"Missing declared transitions: {sorted(missing)}"))

    return tuple(issues)


def assert_valid_twin(twin: ProductionTwin) -> None:
    issues = list(validate_twin(twin))
    if issues:
        raise ProductionTwinValidationError(issues)
