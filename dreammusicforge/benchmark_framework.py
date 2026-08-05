from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, List
import json

REQUIRED_DIMENSIONS = (
    "identity", "hair", "wardrobe", "stage", "camera",
    "lighting", "audio", "lip_sync", "pose", "seam_invisibility",
)

@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]

@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_id: str
    provider_id: str
    provider_version: str
    weighted_score: float
    passed: bool
    failures: List[str]
    metrics: Dict[str, float]
    evidence_hash: str

def load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate_profile(profile: Dict[str, Any]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []
    for field in ("provider_id", "provider_version", "max_duration_seconds", "capabilities"):
        if field not in profile:
            errors.append(f"Missing provider profile field: {field}")
    duration = profile.get("max_duration_seconds")
    if duration is not None and (not isinstance(duration, (int, float)) or duration <= 0):
        errors.append("max_duration_seconds must be a positive number")
    capabilities = profile.get("capabilities", {})
    if capabilities and not isinstance(capabilities, dict):
        errors.append("capabilities must be an object")
    if not profile.get("evidence_status"):
        warnings.append("Provider profile has no evidence_status")
    return ValidationResult(not errors, errors, warnings)

def validate_benchmark(spec: Dict[str, Any]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []
    for field in ("benchmark_id", "name", "duration_seconds", "segments", "dimensions"):
        if field not in spec:
            errors.append(f"Missing benchmark field: {field}")
    segments = spec.get("segments", [])
    if not isinstance(segments, list) or len(segments) < 2:
        errors.append("A continuity benchmark requires at least two segments")
    else:
        ordered = sorted(segments, key=lambda item: float(item.get("start", 0)))
        prior_end = None
        prior_destination = None
        for segment in ordered:
            sid = segment.get("id", "unknown")
            start = float(segment.get("start", 0))
            end = float(segment.get("end", 0))
            if end <= start:
                errors.append(f"{sid} has invalid timing")
            if prior_end is not None and abs(start - prior_end) > 1e-9:
                errors.append(f"{sid} does not begin at the previous segment boundary")
            if prior_destination is not None and segment.get("source_state_id") != prior_destination:
                errors.append(f"{sid} breaks reality-state inheritance")
            prior_end = end
            prior_destination = segment.get("destination_state_id")
    dimensions = spec.get("dimensions", {})
    for name in REQUIRED_DIMENSIONS:
        if name not in dimensions:
            errors.append(f"Missing required benchmark dimension: {name}")
            continue
        rule = dimensions[name]
        weight = rule.get("weight")
        threshold = rule.get("threshold")
        if not isinstance(weight, (int, float)) or weight <= 0:
            errors.append(f"{name}.weight must be positive")
        if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 100:
            errors.append(f"{name}.threshold must be between 0 and 100")
    if dimensions:
        total_weight = sum(float(rule.get("weight", 0)) for rule in dimensions.values())
        if abs(total_weight - 1.0) > 1e-6:
            errors.append(f"Dimension weights must total 1.0, got {total_weight:.6f}")
    return ValidationResult(not errors, errors, warnings)

def verify_provider_fit(spec: Dict[str, Any], profile: Dict[str, Any]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []
    profile_check = validate_profile(profile)
    spec_check = validate_benchmark(spec)
    errors.extend(profile_check.errors)
    errors.extend(spec_check.errors)
    warnings.extend(profile_check.warnings)
    warnings.extend(spec_check.warnings)
    if errors:
        return ValidationResult(False, errors, warnings)
    limit = float(profile["max_duration_seconds"])
    for segment in spec["segments"]:
        duration = float(segment["end"]) - float(segment["start"])
        if duration > limit + 1e-9:
            errors.append(f"{segment['id']} duration {duration:.3f}s exceeds provider limit {limit:.3f}s")
    required = set(spec.get("required_capabilities", []))
    capabilities = profile.get("capabilities", {})
    for capability in sorted(required):
        if not capabilities.get(capability, False):
            errors.append(f"Provider lacks required capability: {capability}")
    return ValidationResult(not errors, errors, warnings)

def score_benchmark(spec: Dict[str, Any], profile: Dict[str, Any], measured_metrics: Dict[str, float]) -> BenchmarkResult:
    fit = verify_provider_fit(spec, profile)
    if not fit.valid:
        raise ValueError("Invalid benchmark execution:\n- " + "\n- ".join(fit.errors))
    failures: List[str] = []
    normalized: Dict[str, float] = {}
    weighted_score = 0.0
    for dimension, rule in spec["dimensions"].items():
        if dimension not in measured_metrics:
            raise ValueError(f"Missing measured metric: {dimension}")
        value = float(measured_metrics[dimension])
        if not 0 <= value <= 100:
            raise ValueError(f"Metric {dimension} must be between 0 and 100")
        normalized[dimension] = round(value, 4)
        weighted_score += value * float(rule["weight"])
        if value < float(rule["threshold"]):
            failures.append(f"{dimension} {value:.2f} < required {float(rule['threshold']):.2f}")
    payload = {
        "benchmark_id": spec["benchmark_id"],
        "provider_id": profile["provider_id"],
        "provider_version": profile["provider_version"],
        "metrics": normalized,
    }
    evidence_hash = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return BenchmarkResult(
        benchmark_id=spec["benchmark_id"],
        provider_id=profile["provider_id"],
        provider_version=profile["provider_version"],
        weighted_score=round(weighted_score, 4),
        passed=not failures,
        failures=failures,
        metrics=normalized,
        evidence_hash=evidence_hash,
    )

def update_capability_profile(profile: Dict[str, Any], results: Iterable[BenchmarkResult]) -> Dict[str, Any]:
    updated = json.loads(json.dumps(profile))
    history = list(updated.setdefault("benchmark_history", []))
    capability_scores = dict(updated.setdefault("measured_scores", {}))
    for result in results:
        history.append({
            "benchmark_id": result.benchmark_id,
            "weighted_score": result.weighted_score,
            "passed": result.passed,
            "evidence_hash": result.evidence_hash,
        })
        for name, score in result.metrics.items():
            existing = capability_scores.get(name, [])
            if not isinstance(existing, list):
                existing = [existing]
            existing.append(score)
            capability_scores[name] = existing
    updated["benchmark_history"] = history
    updated["measured_scores"] = capability_scores
    updated["measured_averages"] = {
        name: round(sum(values) / len(values), 4)
        for name, values in capability_scores.items() if values
    }
    updated["evidence_status"] = "MEASURED"
    return updated

def build_evidence_record(spec: Dict[str, Any], profile: Dict[str, Any], result: BenchmarkResult) -> Dict[str, Any]:
    return {
        "schema_version": "dmf-benchmark-evidence-v0.1",
        "benchmark": {
            "id": spec["benchmark_id"],
            "name": spec["name"],
            "duration_seconds": spec["duration_seconds"],
        },
        "provider": {
            "id": profile["provider_id"],
            "version": profile["provider_version"],
        },
        "result": {
            "passed": result.passed,
            "weighted_score": result.weighted_score,
            "failures": result.failures,
            "metrics": result.metrics,
        },
        "evidence_hash": result.evidence_hash,
        "promotion_decision": "ACCEPT" if result.passed else "REJECT",
    }
