from __future__ import annotations

import json
import logging
from http.cookies import SimpleCookie
from io import BytesIO
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from discord.ext.commands import Context

from .utils.clients.baseclient import HoYoAPIError

if TYPE_CHECKING:
    from bot import Yuzubot

log = logging.getLogger(__name__)


class HoyoLab(commands.Cog):
    def __init__(self, bot: Yuzubot) -> None:
        self.bot: Yuzubot = bot

    @commands.hybrid_command(name="hlregister")
    async def hoyolab_register(self, ctx: Context, user_cookies: str) -> None:
        # Parse Cookies
        content = "Parsing cookies..."
        msg = await ctx.reply(content, ephemeral=True)

        c = SimpleCookie()
        c.load(user_cookies)

        cookies = {}
        target = ["cookie_token_v2", "account_mid_v2", "account_id_v2"]
        for t in target:
            if v := c.get(t):
                cookies[t] = v.value

        if 3 > len(cookies):
            await msg.edit(content=content + "\nWrong cookies")
            return

        # Verify Creds
        content += " ok\nVerifying..."
        await msg.edit(content=content)
        try:
            await self.bot.hoyoclient.verify_l_token(cookies)
        except HoYoAPIError as e:
            await msg.edit(
                content=content + f"\nVerify failed (wrong cookies?)\n```\n{e}```"
            )
            return

        # Fetch Ingame UID
        try:
            record_data = await self.bot.zzzclient.get_game_record(cookies)
        except HoYoAPIError as e:
            await ctx.reply(str(e), ephemeral=True)
            return

        zzz_nickname = record_data.get("nickname") or ""
        zzz_uid = record_data.get("game_role_id") or ""

        content += (
            f" ok\nLogged as {zzz_nickname}({zzz_uid})\n" + "Fetching e_nap_token..."
        )
        await msg.edit(content=content)

        # Fetch e_nap_token
        e_nap_token = await self.bot.zzzclient.get_e_nap_token(cookies, zzz_uid)

        content += f" ok\ne_nap_token preview: `{e_nap_token[:4]}***{e_nap_token[-4:]}`"

        cookies["e_nap_token"] = e_nap_token

        await self.bot.hoyolab_creds_db.execute(
            "INSERT INTO creds VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET zzz_uid = excluded.zzz_uid, cookies = excluded.cookies;",
            (ctx.author.id, zzz_uid, json.dumps(cookies)),
        )
        await self.bot.hoyolab_creds_db.commit()

        content += "\n\nRegister Successful!"
        await msg.edit(content=content)
        log.info(f"{ctx.author} registered as {zzz_nickname}({zzz_uid})")

    @commands.command()
    async def owned(self, ctx: Context) -> None:
        creds_query = await self.bot.hoyolab_creds_db.execute(
            "SELECT * FROM creds WHERE user_id=?", (ctx.author.id,)
        )
        creds = await creds_query.fetchone()
        if creds is None:
            return

        cookies = json.loads(creds[2])
        cookies["e_nap_token"] = await self.bot.zzzclient.get_e_nap_token(
            cookies, creds[1]
        )

        owned = await self.bot.zzzclient.get_owned_agent_list(cookies, creds[1])
        b = BytesIO(json.dumps(owned, indent=2, ensure_ascii=False).encode("utf-8"))
        file = discord.File(b, filename="owned.json")

        await ctx.reply(file=file)

    @commands.command()
    async def detail(self, ctx: Context, agent_id: int) -> None:
        creds_query = await self.bot.hoyolab_creds_db.execute(
            "SELECT * FROM creds WHERE user_id=?", (ctx.author.id,)
        )
        creds = await creds_query.fetchone()
        if creds is None:
            return

        cookies = json.loads(creds[2])
        cookies["e_nap_token"] = await self.bot.zzzclient.get_e_nap_token(
            cookies, creds[1]
        )

        try:
            agent = await self.bot.zzzclient.get_agent_detail(
                cookies, creds[1], agent_id
            )
        except HoYoAPIError as e:
            await ctx.reply(str(e))
            return

        b = BytesIO(json.dumps(agent, indent=2, ensure_ascii=False).encode("utf-8"))
        file = discord.File(b, filename="owned.json")

        await ctx.reply(file=file)


async def setup(bot: Yuzubot):
    await bot.add_cog(HoyoLab(bot))
