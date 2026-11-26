"""Webhook 推送：群消息 / 企业微信机器人，失败重试三次。"""

from __future__ import annotations

import time

import httpx


class WebhookNotifier:
    def __init__(self, url: str, timeout: float = 10.0, retries: int = 3) -> None:
        self.url = url
        self.timeout = timeout
        self.retries = retries

    def send(self, text: str) -> bool:
        if not self.url:
            return False
        payload = {"msgtype": "text", "text": {"content": text}}
        for attempt in range(self.retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(self.url, json=payload)
                    if resp.status_code < 300:
                        return True
            except httpx.HTTPError:
                pass
            time.sleep(0.4 * (2 ** attempt))
        return False
