from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import discord
from discord import ui
from discord.ext import commands
from discord.ext.commands import Context

from .utils import discimg
from .utils.types import Disc

if TYPE_CHECKING:
    from bot import Yuzubot


class BuildCard(commands.Cog):
    def __init__(self, bot: Yuzubot) -> None:
        self.bot: Yuzubot = bot

    @commands.command()
    async def b(self, ctx: Context) -> None:
        with open("./resp.json", "r", encoding="utf-8") as f:
            data = json.loads(f.read())

        container = ui.Container()

        discs = data["data"]["list"][0]["equip"]

        t = ""
        for disc in discs:
            # Name - Level
            t = f"{disc['name']} - Lv{disc['level']}\n"

            # Main Stats
            m = disc["main_properties"][0]
            t += f"-# **{m['property_name']}: {m['base']}**\n"

            # Sub Stats
            for p in disc["properties"]:
                t += f"-# {p['property_name']}{f' (+{p["add"]})' if int(p['add']) else ''}: {p['base']}\n"

            section = ui.Section(
                ui.TextDisplay(t), accessory=ui.Thumbnail(disc["icon"])
            )
            container.add_item(section)
            container.add_item(ui.Separator())

        view = ui.LayoutView()
        view.add_item(container)
        await ctx.reply(view=view)

    @commands.command()
    async def g(self, ctx: Context) -> None:
        creds_query = await self.bot.hoyolab_creds_db.execute(
            "SELECT * FROM creds WHERE user_id=?", (ctx.author.id,)
        )
        creds = await creds_query.fetchone()
        if creds is None:
            return

        cookies = json.loads(creds[2])
        print(cookies)
        cookies["e_nap_token"] = await self.bot.zzzclient.get_e_nap_token(
            cookies, creds[1]
        )
        data = await self.bot.zzzclient.get_agent_detail(cookies, creds[1], 1431)
        agent = data["data"]["list"][0]

        container = ui.Container()

        main_text_raw = f"""# {agent["avatar"]["full_name_mi18n"]}\n"""

        stats_text_raw = ""
        for i, p in enumerate(agent["avatar"]["properties"]):
            stats_text_raw += f"> -# {p['property_name']}: {p['final']}\n"

        main_text_raw += stats_text_raw

        main_text = ui.TextDisplay(main_text_raw)

        icon_url = f"https://act-webstatic.hoyoverse.com/game_record/zzzv2/role_square_avatar/role_square_avatar_{agent['avatar']['id']}.png"
        section1 = ui.Section(main_text, accessory=ui.Thumbnail(icon_url))
        container.add_item(section1)

        container.add_item(ui.Separator())

        media_gallery = ui.MediaGallery()
        files = []

        discs: list[Disc] = agent["equip"]

        for i, disc in enumerate(discs):
            img = await asyncio.to_thread(discimg.generate_disc_image, disc)
            file = discord.File(img, f"disc{i}.png")
            files.append(file)
            media_gallery.add_item(media=file)

        container.add_item(media_gallery)

        view = ui.LayoutView()
        view.add_item(container)

        await ctx.reply(view=view, files=files)

    @commands.command()
    async def testimg(self, ctx: Context) -> None:
        with open("./resp.json", "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        img_bytes = discimg.generate_disc_image(data["data"]["list"][0]["equip"][0])
        file = discord.File(img_bytes, "disc.png")
        await ctx.reply(file=file)


async def setup(bot: Yuzubot):
    await bot.add_cog(BuildCard(bot))
