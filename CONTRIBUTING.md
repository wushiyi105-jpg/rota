# 贡献指南

## 本地开发

```bash
uv sync --extra dev
uv run python -m rota seed
uv run python -m rota plan --month 2026-12
```

提交前必须四条全绿：

```bash
uv run ruff check .
uv run mypy rota
uv run pytest -q
uv run python -m rota doctor
```

## 分层约定

- `domain/` 只放纯函数与 dataclass，不 import httpx / sqlalchemy / fastapi。
- `ports/` 只放 Protocol，`adapters/` 才认识具体库。
- `app/` 编排用例，`iface/` 只做参数解析与渲染。
- 新增一条规则：在 `domain/rules/` 建文件、给唯一 `rule_id`、在 `engine.evaluate` 里接上、在 `tests/` 至少一条断言。
- 让模型多说一句话之前，先想清楚守卫怎么拦。

## 报 bug

请附上：`python -m rota doctor` 输出、`plan --json` 的输出、与你预期不符的那一天。不要贴真实员工姓名。
