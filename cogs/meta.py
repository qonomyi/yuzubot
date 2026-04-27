from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from discord.ext.commands import Context

if TYPE_CHECKING:
    from bot import Yuzubot

log = logging.getLogger(__name__)


class MetaCog(commands.Cog):
    def __init__(self, bot: Yuzubot) -> None:
        self.bot: Yuzubot = bot

    @commands.hybrid_command(description="About this bot")
    async def info(self, ctx: Context) -> None:
        embed = discord.Embed(
            title="// Yuzubot Information",
            description=(
                "Yuzubot is a helper bot for Zenless Zone Zero / HoYoLAB\n"
                "･ [Source Code](https://github.com/qonomyi/yuzubot)"
            ),
            color=0xB92733,
        )

        embed.add_field(
            name="Last Restart",
            value=f"<t:{self.bot.start_time}:f>\n(<t:{self.bot.start_time}:R>)",
        )
        embed.add_field(
            name="Assets Last Updated",
            value=f"<t:{self.bot.assets_last_updated}:f>\n(<t:{self.bot.assets_last_updated}:R>)",
        )

        assert self.bot.user is not None
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # self.bot.userにはbannerが含まれていないため、fetchで取得する
        user = await self.bot.fetch_user(self.bot.user.id)
        if banner := user.banner:
            embed.set_image(url=banner.url)

        embed.set_footer(
            text='"Zenless Zone Zero" and all related assets are trademarks and property of HoYoverse.'
        )

        await ctx.reply(embed=embed)


async def setup(bot: Yuzubot):
    await bot.add_cog(MetaCog(bot))
