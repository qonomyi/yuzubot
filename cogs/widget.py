from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context

import config
from cogs.utils.hoyocreds import HoYoCredsNotFoundError
from cogs.utils.types import HoYoCreds

if TYPE_CHECKING:
    from bot import Yuzubot

log = logging.getLogger(__name__)


class WidgetCog(commands.Cog):
    def __init__(self, bot: Yuzubot) -> None:
        self.bot: Yuzubot = bot

    @commands.hybrid_group("widget")
    async def widget(self, ctx: Context):
        pass

    @widget.command(name="setup")
    async def widget_setup(self, ctx: Context) -> None:
        pass

    @widget.command(name="refresh")
    async def widget_refresh(self, ctx: Context) -> None:
        await ctx.defer()
        result, payload = await self.sync_user_discord_widget(ctx.author.id)
        if result is True:
            await ctx.reply("ok", ephemeral=True)
        else:
            await ctx.reply("something went wrong", ephemeral=True)

    async def sync_user_discord_widget(self, user_id: int) -> (bool, payload):
        creds: HoYoCreds = await self.bot.hoyolab_creds.get(user_id)

        token = config.token
        application_id = self.bot.application_id

        zzz_record_card = await self.bot.zzzclient.get_game_record(creds["cookies"])

        ingame_level = str(zzz_record_card["level"])
        ingame_name = str(zzz_record_card["nickname"])

        # hardcoded index cuz data list is i18n'd
        # (just change language to english might fix this, but uhh im lazy)
        active_days_count = str(zzz_record_card["data"][0]["value"])
        achievements_count = str(zzz_record_card["data"][1]["value"])
        agents_count = str(zzz_record_card["data"][2]["value"])

        da_detail = await self.bot.zzzclient.get_da_detail(
            creds["cookies"], creds["zzz_uid"]
        )
        da_total_score = str(da_detail["data"]["total_score"])

        shiyu_detail = await self.bot.zzzclient.get_shiyu_detail(
            creds["cookies"], creds["zzz_uid"]
        )
        shiyu_total_score = str(shiyu_detail["data"]["total_score"])

        dynamic_data = [
            {"type": 1, "name": "ingame_name", "value": ingame_name},
            {"type": 1, "name": "top_subtitle_1", "value": "Yuzuha my beloved..."},
            {"type": 1, "name": "interknot_level", "value": ingame_level},
            {"type": 1, "name": "achievements_count", "value": achievements_count},
            {"type": 1, "name": "agents_count", "value": agents_count},
            {"type": 1, "name": "deadly_assault_score", "value": da_total_score},
            {"type": 1, "name": "shiyu_defence_score", "value": shiyu_total_score},
            {"type": 1, "name": "active_days_count", "value": active_days_count},
            {
                "type": 1,
                "name": "mini_text",
                "value": f"{ingame_name} ･ Lv{ingame_level}",
            },
            {
                "type": 3,
                "name": "hero_image",
                "value": {
                    "url": "https://act-webstatic.hoyoverse.com/game_record/zzzv2/role_teaser_avatar/role_teaser_avatar_1411.png"
                },
            },
        ]

        payload = {"username": ingame_name, "data": {"dynamic": dynamic_data}}
        url = f"https://discord.com/api/v9/applications/{application_id}/users/{user_id}/identities/0/profile"

        log.info(payload)

        async with aiohttp.ClientSession(
            headers={
                "Authorization": f"Bot {token}",
                "Content-Type": "application/json",
            }
        ) as session:
            async with session.patch(
                url, data=json.dumps(payload, ensure_ascii=True)
            ) as resp:
                if resp.status != 204:
                    return (False, payload)

        return (True, payload)


async def setup(bot: Yuzubot):
    await bot.add_cog(WidgetCog(bot))
