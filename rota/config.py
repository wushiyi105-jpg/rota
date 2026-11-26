"""配置：pydantic-settings，默认值直接可跑。"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ROTA_", extra="ignore")

    db_path: Path = Path("data/rota.db")
    port: int = 8001
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    llm_model: str = "deepseek-flash"
    webhook_url: str = ""
    # 约束权重
    weight_fairness: int = 10
    weight_rest: int = 8
    weight_consecutive: int = 6
    weight_skill: int = 15
    max_consecutive_days: int = 5
    min_rest_hours: int = 11
    # 班次需求："kind[:required_skill]" 逗号分隔
    slots: str = "morning:收银,evening:,night:夜班"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def slot_specs(self) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for item in self.slots.split(","):
            if not item.strip():
                continue
            kind, _, skill = item.partition(":")
            out.append((kind.strip(), skill.strip()))
        return out


settings = Settings()
