from __future__ import annotations

from bot.protocol.base import Model


class Cmd(Model):
    name: str
    raw: str
    arg: str


__all__ = ["Cmd"]
