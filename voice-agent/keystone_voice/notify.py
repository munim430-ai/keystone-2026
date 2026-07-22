"""Optional Telegram notifications for hot leads and errors."""
from __future__ import annotations

import httpx

from .config import Config


class Notifier:
    def __init__(self, cfg: Config):
        self.token = cfg.telegram_bot_token
        self.chat_id = cfg.telegram_chat_id
        self.enabled = bool(self.token and self.chat_id)

    async def send(self, text: str) -> None:
        if not self.enabled:
            return
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                await client.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json={"chat_id": self.chat_id, "text": text,
                          "parse_mode": "HTML", "disable_web_page_preview": True},
                )
        except Exception:
            pass  # notifications are best-effort, never block a call
