from __future__ import annotations

import json
from http.cookies import SimpleCookie
from typing import TYPE_CHECKING

from discord.ext import commands
from discord.ext.commands import Context

from cogs.utils.hoyoclient import HoYoAPIError

if TYPE_CHECKING:
    from bot import Yuzubot


class HoyoLab(commands.Cog):
    def __init__(self, bot: Yuzubot) -> None:
        self.bot: Yuzubot = bot

    @commands.hybrid_command(name="hlregister")
    async def hoyolab_login(self, ctx: Context, user_cookies: str) -> None:
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
            data = await self.bot.zzzclient.get_game_record(cookies)
        except HoYoAPIError as e:
            await ctx.reply(str(e), ephemeral=True)
            return

        zzz_uid = data.get("game_role_id") or ""

        content += (
            f" ok\nLogged as {data.get('nickname')}({zzz_uid})\n"
            + "Fetching e_nap_token..."
        )
        await msg.edit(content=content)

        # Fetch e_nap_token
        e_nap_token = await self.bot.zzzclient.get_e_nap_token(cookies, zzz_uid)

        content += f" ok\ne_nap_token preview: `{e_nap_token[:4]}***{e_nap_token[-4:]}`"

        cookies["e_nap_token"] = e_nap_token

        await self.bot.hoyolab_creds_db.execute(
            "INSERT INTO creds VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET cookies = excluded.cookies;",
            (ctx.author.id, json.dumps(cookies)),
        )
        await self.bot.hoyolab_creds_db.commit()

        content += "\n\nRegister Successful!"
        await msg.edit(content=content)


async def setup(bot: Yuzubot):
    await bot.add_cog(HoyoLab(bot))
