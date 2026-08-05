from __future__ import annotations

import argparse
import json
from pathlib import Path

from dreammusicforge.benchmark_framework import (
    build_evidence_record,
    load_json,
    score_benchmark,
    update_capability_profile,
    verify_provider_fit,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a DreamMusicForge renderer benchmark.")
    parser.add_argument("benchmark")
    parser.add_argument("profile")
    parser.add_argument("metrics")
    parser.add_argument("--evidence-out", required=True)
    parser.add_argument("--profile-out", required=True)
    args = parser.parse_args()

    spec = load_json(args.benchmark)
    profile = load_json(args.profile)
    metrics = load_json(args.metrics)

    fit = verify_provider_fit(spec, profile)
    if not fit.valid:
        print("PROVIDER FIT FAILED")
        for error in fit.errors:
            print(f"- {error}")
        return 2

    result = score_benchmark(spec, profile, metrics)
    evidence = build_evidence_record(spec, profile, result)
    updated_profile = update_capability_profile(profile, [result])

    evidence_path = Path(args.evidence_out)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    profile_path = Path(args.profile_out)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(updated_profile, indent=2), encoding="utf-8")

    print(f"{'PASS' if result.passed else 'FAIL'}: {result.weighted_score:.2f}")
    for failure in result.failures:
        print(f"- {failure}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
