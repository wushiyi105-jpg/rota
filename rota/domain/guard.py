"""守卫：模型只能把已有扣分说成人话，不能带出新数字、新日期、名单外的人。

做法很直接——把模型输出里出现的数字、日期、姓名逐个对照事实；
只要有一个对不上，整段丢弃，退回离线解释。
"""

from __future__ import annotations

import re

_NUM = re.compile(r"\d+(?:\.\d+)?")
_DATE = re.compile(r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}月\d{1,2}[日号]")
_NAME = re.compile(r"(?:换给|换由|交给|给|由|让)([\u4e00-\u9fff]{2,3})")
_PRONOUNS = {"他", "她", "它", "大家", "别人", "自己", "新人", "对方", "某人", "其他人"}


def guard_text(text: str, facts: str, names: list[str]) -> tuple[str, str | None]:
    """返回 (可用文本, 丢弃原因)。可用时原因为 None。"""
    body = (text or "").strip()
    if not body:
        return "", "模型返回为空"

    allowed_dates = set(_DATE.findall(facts))
    for d in _DATE.findall(body):
        if d not in allowed_dates:
            return "", f"模型写出了事实里没有的日期：{d}"

    allowed_numbers = set(_NUM.findall(_DATE.sub(" ", facts)))
    for n in _NUM.findall(_DATE.sub(" ", body)):
        if n not in allowed_numbers:
            return "", f"模型写出了事实里没有的数字：{n}"

    roster = set(names)
    for cand in _NAME.findall(body):
        if cand not in roster and cand not in _PRONOUNS:
            return "", f"模型写出了名单外的人：{cand}"

    return body, None
