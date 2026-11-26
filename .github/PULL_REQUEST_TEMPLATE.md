## 改了什么

<!-- 一句话 -->

## 为什么

<!-- 关联 issue：Fixes #  -->

## 自查

- [ ] `ruff check .` 通过
- [ ] `mypy rota` 通过
- [ ] `pytest -q` 通过（新规则补了断言）
- [ ] `python -m rota doctor` 退出码 0
- [ ] 新增依赖已在 README「依赖说明」写一行
- [ ] 没有在 `cli.py` / `web.py` 里写业务规则
- [ ] 模型输出新增字段有守卫与测试
