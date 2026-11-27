"""主用例只依赖 ports：用 MagicMock 内存假实现，不建 SQLite 文件。"""

from __future__ import annotations

from unittest.mock import MagicMock

from rota.app.run import plan_month
from rota.config import Settings
from rota.ports import StorePort


def test_main_path_with_memory_store(tmp_path) -> None:
    store = MagicMock(spec=StorePort)
    store.list_staff.return_value = []
    store.list_leaves.return_value = []
    
    out = plan_month(store, Settings(), "2026-12")
    assert out is not None
    assert not (tmp_path / "app.db").exists()
