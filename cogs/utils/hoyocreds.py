from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING

import aiosqlite

import config
from cogs.utils import cipher
from cogs.utils.types import HoYoCreds, HoYoCredsRaw

if TYPE_CHECKING:
    from bot import Yuzubot

log = logging.getLogger(__name__)


class HoYoCredsNotFoundError(Exception):
    def __init__(self, user_id: str | int) -> None:
        super().__init__(f"No credential found for User: {user_id}")


class HoYoCredsDBHelper:
    def __init__(self, bot: Yuzubot, db_conn: aiosqlite.Connection) -> None:
        self.bot = bot
        self.db = db_conn

        if not config.encrypt_db:
            log.warn("Credential DB encryption is disabled!!")

    async def init_db(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS creds (
             user_id TEXT PRIMARY KEY,
             user_data TEXT,
             e_nap_token_expires_at INTEGER,
             e_nap_token_is_expired BOOLEAN
        )
        """

        await self.db.execute(query)
        await self.db.commit()

        log.info("HoYoCredsDB Initialized")

    async def query(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        return await self.db.execute(query, params)

    async def register(self, user_data: HoYoCredsRaw) -> bool:
        query = """
        INSERT INTO creds VALUES
            (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            user_data = excluded.user_data;
        """
        if config.encrypt_db:
            user_id = cipher.hash_user_id(user_data["user_id"])
            data = cipher.encrypt_user_data(user_data)
        else:
            user_id = user_data["user_id"]
            data = json.dumps(user_data)

        expires_at = int(time.time()) + (3600 * 47)
        await self.db.execute(
            query,
            (user_id, data, expires_at, False),
        )
        await self.db.commit()

        return True

    async def get(self, user_id: int) -> HoYoCreds:
        hashed_user_id = cipher.hash_user_id(user_id)
        cur = await self.db.execute(
            "SELECT * FROM creds WHERE user_id=?", (hashed_user_id,)
        )
        row = await cur.fetchone()

        if row is None:
            raise HoYoCredsNotFoundError(user_id)

        user_data_raw = row["user_data"]

        if config.encrypt_db:
            user_data: HoYoCredsRaw = cipher.decrypt_user_data(user_data_raw)
        else:
            user_data = json.loads(user_data_raw)

        return {
            "user_id": user_data["user_id"],
            "zzz_uid": user_data["zzz_uid"],
            "cookies": json.loads(user_data["cookies"]),
        }

    async def get_zzz(self, user_id: int) -> HoYoCreds:
        # returns credentials with refreshed e_nap_token
        creds: HoYoCreds = await self.get(user_id)

        e_nap_token = await self.bot.zzzclient.get_e_nap_token(
            creds["cookies"], creds["zzz_uid"]
        )

        creds["cookies"]["e_nap_token"] = e_nap_token

        if e_nap_token:
            await self.update_e_nap_token_expire(user_id, False)
        else:
            await self.update_e_nap_token_expire(user_id, True)

        return creds

    async def update_e_nap_token_expire(self, raw_user_id: int, is_expired: bool):
        expires_at = 0
        if not is_expired:
            expires_at = int(time.time()) + (3600 * 47)

        user_id = raw_user_id

        if config.encrypt_db:
            user_id = cipher.hash_user_id(user_id)

        query = """
        UPDATE creds SET 
            e_nap_token_expires_at = ?,
            e_nap_token_is_expired = ?
        WHERE user_id = ?
        """
        await self.db.execute(query, (expires_at, is_expired, user_id))
        await self.db.commit()

    async def refresh_e_nap_token(self) -> tuple[int, int]:
        refreshed_count = 0
        expired_count = 0

        query = """
        SELECT * FROM creds 
        WHERE e_nap_token_expires_at < ? AND e_nap_token_is_expired = 0
        """
        cur = await self.query(query, (int(time.time()),))

        for row in await cur.fetchall():
            user_data_raw = row["user_data"]
            if config.encrypt_db:
                user_data: HoYoCredsRaw = cipher.decrypt_user_data(user_data_raw)
            else:
                user_data = json.loads(user_data_raw)

            e_nap_token = await self.bot.zzzclient.get_e_nap_token(
                json.loads(user_data["cookies"]), user_data["zzz_uid"]
            )

            if e_nap_token:
                await self.update_e_nap_token_expire(user_data["user_id"], False)
                refreshed_count += 1
            else:
                await self.update_e_nap_token_expire(user_data["user_id"], True)
                expired_count += 1

        return (refreshed_count, expired_count)
