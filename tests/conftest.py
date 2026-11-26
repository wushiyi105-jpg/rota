from __future__ import annotations

import pytest

from rota.config import Settings
from rota.domain.models import Staff


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(db_path=tmp_path / "rota.db", llm_api_key="", webhook_url="")


@pytest.fixture
def staff() -> list[Staff]:
    return [
        Staff(1, "阿泽", frozenset({"收银", "夜班"})),
        Staff(2, "小林", frozenset({"收银"})),
        Staff(3, "文文", frozenset({"夜班"})),
        Staff(4, "大刘"),
    ]
