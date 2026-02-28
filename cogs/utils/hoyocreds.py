from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import aiosqlite

if TYPE_CHECKING:
    from bot import Yuzubot

log = logging.getLogger(__name__)


class HoYoCredsDBHelper:
    def __init__(self, bot: Yuzubot, db_conn: aiosqlite.Connection) -> None:
        self.bot = bot
        self.db = db_conn

    async def init_db(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS creds ( 
             user_id INTEGER PRIMARY KEY,
             zzz_uid INTEGER,
             cookies TEXT
        )
        """

        await self.db.execute(query)
        await self.db.commit()

        log.info("HoYoCredsDB Initialized")

    async def get(self, user_id: int) -> dict | None:
        cur = await self.db.execute("SELECT * FROM creds WHERE user_id=?", (user_id,))
        row = await cur.fetchone()

        if row is None:
            return None

        return {
            "user_id": row["user_id"],
            "zzz_uid": row["zzz_uid"],
            "cookies": json.loads(row["cookies"]),
        }

    async def get_zzz(self, user_id: int) -> dict | None:
        # returns credentials with refreshed e_nap_token
        creds = await self.get(user_id)
        if creds is None:
            return

        e_nap_token = await self.bot.zzzclient.get_e_nap_token(
            creds["cookies"], creds["zzz_uid"]
        )

        creds["cookies"]["e_nap_token"] = e_nap_token

        return creds
