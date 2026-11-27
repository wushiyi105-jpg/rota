# 更新记录

## Unreleased

- `0001_init` 改为显式 `op.create_table` / `op.create_index`，运行期走 `alembic upgrade`
- `app/` 只依赖 `ports`，新增内存假实现用例
- 开 ruff `E2`/`E3`；CI 增加 `docker build` 与 `/health` 探活

## 1.0.0

首个版本，新栈实现（FastAPI + Typer + SQLAlchemy + Alembic）。

- 六条可解释约束：`fairness.spread`、`rest.night_to_morning`、`consecutive.over_limit`、`coverage.gap`、`leave.conflict`、`skill.mismatch`、`load.double_booked`
- 求解器支持 `keep`：插入请假后只重排受影响的日子，并输出变更 diff
- 导出：ICS（夜班跨天）、CSV、人均班次、群消息
- `jobs` 表 + 幂等键：每日到期提醒，失败保留待重试
- 模型只做解释，输出经守卫校验（事实外数字 / 日期 / 人名整段丢弃）
- CLI：`seed` / `plan` / `show` / `replan` / `comment` / `export` / `jobs` / `doctor` / `web`
- Web：整月表、插请假重排、三种导出、扣分解释
- `doctor`：配置 / 数据库 / 模型 / webhook 四项体检
- 59 条测试，覆盖率 82%
