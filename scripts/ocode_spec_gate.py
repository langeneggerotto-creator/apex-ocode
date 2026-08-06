from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "CLAUDE.md",
    "ocode-platform-spec/README.md",
    "ocode-platform-spec/FULL_PLATFORM_SPEC.md",
    "ocode-platform-spec/BITE_ROADMAP.md",
    "ocode-platform-spec/SECURITY_DEPLOYMENT.md",
    "ocode-platform-spec/CLAUDE_CODE_MASTER_PROMPT.md",
]


def main() -> int:
    failures: list[str] = []

    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"missing or empty: {relative}")

    roadmap = ROOT / "ocode-platform-spec/BITE_ROADMAP.md"
    if roadmap.is_file():
        text = roadmap.read_text(encoding="utf-8")
        for bite in range(1, 14):
            marker = f"Bite {bite}"
            if marker not in text:
                failures.append(f"roadmap missing {marker}")

    contract = ROOT / "CLAUDE.md"
    if contract.is_file():
        text = contract.read_text(encoding="utf-8")
        required_rules = [
            "one bite at a time",
            "Never claim a capability without executable evidence",
            "Fail closed",
        ]
        for rule in required_rules:
            if rule.lower() not in text.lower():
                failures.append(f"Claude contract missing rule: {rule}")

    if failures:
        print("OCODE SPEC GATE: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("OCODE SPEC GATE: PASS")
    print(f"- required files: {len(REQUIRED)}")
    print("- roadmap bites: 13")
    print("- Claude Code contract: present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
