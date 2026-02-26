from __future__ import annotations

import aiohttp
import aiosqlite
import discord
from discord.ext import commands

import config
from cogs.utils.hoyoclient import HoYoClient
from cogs.utils.zzzclient import ZZZClient

initial_extensions = (
    "cogs.buildcard",
    "cogs.hoyolab",
)


class Yuzubot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__("y:", intents=intents)

    async def on_ready(self):
        print("Ready")

    async def setup_hook(self) -> None:
        self.hoyolab_creds_db = await aiosqlite.connect("./data/hoyolab_creds.db")
        await self.hoyolab_creds_db.execute(
            "CREATE TABLE IF NOT EXISTS creds("
            + "user_id INTEGER PRIMARY KEY,"
            + "cookies TEXT)"
        )
        await self.hoyolab_creds_db.commit()

        self.session = aiohttp.ClientSession(
            cookie_jar=aiohttp.cookiejar.DummyCookieJar()
        )
        self.hoyoclient = HoYoClient(self.session)
        self.zzzclient = ZZZClient(self.session)

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                print(e)
                print(f"Failed to load extension {extension}.")
        await self.load_extension("jishaku")

    async def close(self) -> None:
        await self.session.close()
        await self.hoyolab_creds_db.close()
        await super().close()


bot = Yuzubot()
bot.run(config.token)
