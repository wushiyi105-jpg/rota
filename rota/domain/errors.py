"""领域异常：模型调用的通用失败，不依赖具体 SDK。"""

from __future__ import annotations


class LLMError(RuntimeError):
    """模型调用失败（网络、鉴权、返回不可解析）。"""
