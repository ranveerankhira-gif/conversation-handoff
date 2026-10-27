#!/usr/bin/env python3
"""Build the stable public catalog for the conversation-handoff repository."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
NAMES = ["conversation-handoff"]
PURPOSE = {
    "conversation-handoff": "创建、核验或恢复包含完整可见记录与详细工作记忆的长对话交接包",
}
WRITES = {"conversation-handoff"}
CREDENTIALS = {"conversation-handoff"}
COST = set()
DEPENDENCIES = {
    "conversation-handoff": [
        "Python 3.10+",
        "完整的用户提供 JSONL，或当前宿主可访问的明确 Codex 会话",
        "可选：人工检查导出图片中的文字秘密",
    ],
}


def display_name(name: str) -> str:
    text = (SKILLS / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
    match = re.search(r'^\s*display_name:\s*["\']?(.+?)["\']?\s*$', text, re.M)
    return match.group(1) if match else name


def main() -> int:
    provenance = json.loads((ROOT / "provenance.json").read_text(encoding="utf-8"))
    approved = {row["name"] for row in provenance.get("skills", [])}
    planned = set(NAMES)
    directories = {path.name for path in SKILLS.iterdir() if path.is_dir()}
    if approved != planned or directories != approved:
        raise ValueError(
            "publication set differs from provenance approval: "
            f"unplanned={sorted(directories - approved)}, "
            f"missing={sorted(approved - directories)}, "
            f"metadata_gap={sorted(approved ^ planned)}"
        )
    rows = []
    for name in NAMES:
        rows.append({
            "name": name,
            "display_name_zh": display_name(name),
            "purpose_zh": PURPOSE[name],
            "release": "v0.1.0",
            "platforms": ["cross-platform"],
            "risk_level": "high",
            "permissions": {
                "network": False,
                "filesystem_read": True,
                "filesystem_write": name in WRITES,
                "credentials": name in CREDENTIALS,
                "external_state": False,
                "cost_or_quota": name in COST,
            },
            "dependencies": DEPENDENCIES[name],
            "invocation_policy": "explicit-only",
            "license": "MIT",
            "version": "0.1.0",
            "archive_sha256": None,
        })
    payload = {
        "schema_version": 1,
        "repository": "ranveerankhira-gif/conversation-handoff",
        "skills": rows,
    }
    target = ROOT / "catalog.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target} with {len(rows)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

