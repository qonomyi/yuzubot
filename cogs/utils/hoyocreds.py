from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import aiosqlite

from cogs.utils import cipher
from cogs.utils.types import HoYoUserData

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
             user_id TEXT PRIMARY KEY,
             user_data TEXT
        )
        """

        await self.db.execute(query)
        await self.db.commit()

        log.info("HoYoCredsDB Initialized")

    async def register(self, user_data: HoYoUserData) -> bool:
        query = """
        INSERT INTO creds VALUES 
            (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            user_data = excluded.user_data;
        """
        hashed_id = cipher.hash_user_id(user_data["user_id"])
        encrypted_data = cipher.encrypt_user_data(user_data)

        await self.db.execute(
            query,
            (hashed_id, encrypted_data),
        )
        await self.db.commit()

        return True

    async def get(self, user_id: int) -> dict | None:
        hashed_user_id = cipher.hash_user_id(user_id)
        cur = await self.db.execute(
            "SELECT * FROM creds WHERE user_id=?", (hashed_user_id,)
        )
        row = await cur.fetchone()

        if row is None:
            return None

        user_data_raw = row["user_data"]
        user_data: HoYoUserData = cipher.decrypt_user_data(user_data_raw)

        return {
            "user_id": user_data["user_id"],
            "zzz_uid": user_data["zzz_uid"],
            "cookies": json.loads(user_data["cookies"]),
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
