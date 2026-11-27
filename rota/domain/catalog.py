"""门店模板与劳动规则库。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def templates() -> list[dict[str, Any]]:
    return json.loads((ROOT / "data" / "store_templates.json").read_text(encoding="utf-8"))["templates"]


@lru_cache(maxsize=1)
def rules() -> list[dict[str, Any]]:
    return json.loads((ROOT / "data" / "labor_rules.json").read_text(encoding="utf-8"))["rules"]


def match_template(team: str) -> dict[str, Any]:
    for template in templates():
        if any(hint in team for hint in template["team_hint"]):
            return template
    return templates()[0]
