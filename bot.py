from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

import aiohttp
import aiosqlite
import discord
from discord.ext import commands

import config
from cogs.utils.clients import HoYoClient, ZZZClient
from cogs.utils.hoyocreds import HoYoCredsDBHelper
from cogs.utils.zzzemoji import ZZZEmojiHelper

log = logging.getLogger(__name__)


initial_extensions = (
    "cogs.buildcard",
    "cogs.hoyolab",
)


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
    )

    file_handler = RotatingFileHandler(
        filename="yuzubot.log",
        encoding="utf-8",
        maxBytes=32 * 1024 * 1024,  # 32MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


class Yuzubot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__("y:", intents=intents)

    async def on_ready(self):
        assert self.user
        log.info(f"Logged as {self.user} ({self.user.id})")

    async def setup_hook(self) -> None:
        self._hoyolab_creds_db = await aiosqlite.connect("./data/hoyolab_creds.db")
        self._hoyolab_creds_db.row_factory = aiosqlite.Row

        self.hoyolab_creds = HoYoCredsDBHelper(self, self._hoyolab_creds_db)
        await self.hoyolab_creds.init_db()

        self.session = aiohttp.ClientSession(
            cookie_jar=aiohttp.cookiejar.DummyCookieJar()
        )
        self.hoyoclient = HoYoClient(self.session)
        self.zzzclient = ZZZClient(self.session)

        self.zzzemoji = ZZZEmojiHelper(self)
        await self.zzzemoji.emoji_init()
        await self.zzzemoji.data_init()

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                log.exception(e)
                log.exception(f"Failed to load extension {extension}.")
        await self.load_extension("jishaku")

    async def close(self) -> None:
        await self.session.close()
        await self._hoyolab_creds_db.close()
        await super().close()


setup_logging()

bot = Yuzubot()
bot.run(config.token, log_handler=None)
