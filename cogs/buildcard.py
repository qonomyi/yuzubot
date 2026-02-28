from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING

import discord
from discord import ui
from discord.ext import commands
from discord.ext.commands import Context

from .utils import discimg
from .utils.types import Disc, DiscProperty

log = logging.getLogger(__name__)

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

    @commands.hybrid_command()
    async def buildcard(self, ctx: Context, agent_id: int) -> None:
        await ctx.defer()
        start_time = time.time()
        creds = await self.bot.hoyolab_creds.get_zzz(ctx.author.id)

        if creds is None:
            await ctx.reply("no credential info found in db")
            return

        agent = await self.bot.zzzclient.get_agent_detail(
            creds["cookies"], creds["zzz_uid"], agent_id
        )

        icon_info = await self.bot.zzzclient.get_icon_info(creds["cookies"])
        agent_color_raw = icon_info["avatar_icon"][str(agent_id)][
            "vertical_painting_color"
        ]
        agent_color = discord.Colour.from_str(agent_color_raw)

        container = ui.Container(accent_color=agent_color)

        rarity_icon_emoji = str(
            await self.bot.zzzemoji.get_rarity_emoji(
                agent["avatar"]["rarity"], icon=True
            )
        )

        element_emoji = (
            str(
                await self.bot.zzzemoji.get_element_emoji(
                    agent["avatar"]["element_type"], agent["avatar"]["sub_element_type"]
                )
            )
            or ""
        )

        profession_emoji = (
            str(
                await self.bot.zzzemoji.get_profession_emoji(
                    agent["avatar"]["avatar_profession"]
                )
            )
            or ""
        )

        # Main Stats
        main_text_raw = (
            f"# {rarity_icon_emoji} {agent['avatar']['name_mi18n']} {element_emoji}{profession_emoji}\n"
            + f"-# Lvl {agent['avatar']['level']} ･ Mindscape {agent['avatar']['rank']}\n"
        )

        stats_text = ""
        for i, p in enumerate(agent["avatar"]["properties"]):
            prop_name = p["property_name"]
            prop_emoji = (
                str(await self.bot.zzzemoji.get_prop_emoji(p["property_id"])) or ""
            )

            stats_text += f"> {prop_emoji} {prop_name}: {p['final']}\n"

        main_text_raw += stats_text
        main_text = ui.TextDisplay(main_text_raw)

        icon_url = f"https://act-webstatic.hoyoverse.com/game_record/zzzv2/role_square_avatar/role_square_avatar_{agent['avatar']['id']}.png"
        stats_section = ui.Section(main_text, accessory=ui.Thumbnail(icon_url))
        container.add_item(stats_section)

        container.add_item(ui.Separator())

        # W-Engine
        we = agent.get("weapon")
        if we is None:
            pass
        else:
            we_rarity_emoji = str(
                await self.bot.zzzemoji.get_rarity_emoji(we["rarity"], icon=False)
            )

            we_name = we["name"]
            we_prop = we["properties"][0]
            we_sub_prop = we["main_properties"][0]
            we_text_raw = (
                f"## {we_rarity_emoji} {we_name}\n"
                + f"-# Lvl {we['level']} ･ Phase {we['star']}\n"
                + f"> {we_prop['property_name']}: {we_prop['base']} ･ "
                + f"{we_sub_prop['property_name']}: {we_sub_prop['base']}\n"
            )

            we_text = ui.TextDisplay(we_text_raw)
            we_thumbnail = ui.Thumbnail(we["icon"])
            we_section = ui.Section(we_text, accessory=we_thumbnail)

            container.add_item(we_section)

            container.add_item(ui.Separator())

        # Skills
        skills = agent["avatar"]["skills"]
        skills_text_raw = ""
        for skill in skills:
            skill_emoji = str(
                await self.bot.zzzemoji.get_skill_emoji(skill["skill_type"])
            )
            skills_text_raw += f"{skill_emoji} {skill['level']} | "

        skills_text_raw = skills_text_raw[:-2]
        skills_text = ui.TextDisplay(skills_text_raw)
        container.add_item(skills_text)
        container.add_item(ui.Separator())

        # Disc
        disc_media_gallery = ui.MediaGallery()
        files = []

        discs: list[Disc] = agent["equip"]

        total_disc_score = 0.0
        for i, disc in enumerate(discs):
            # Calc score
            hit_count = 0
            max_hit_count = 5

            substats: list[DiscProperty] = disc["properties"]
            for s in substats:
                if s["valid"]:
                    hit_count += s["level"]
                    max_hit_count += 1

            if disc["main_properties"][0]["valid"]:
                hit_count += 1
                max_hit_count += 1

            total_disc_score += hit_count / max_hit_count * 100

            # Disc image
            img = await asyncio.to_thread(discimg.generate_disc_image, disc)
            file = discord.File(img, f"disc{i}.png")
            files.append(file)
            disc_media_gallery.add_item(media=file)

        disc_score_button = ui.Button(label=f"{total_disc_score:.1f}", disabled=True)
        disc_score_section = ui.Section(
            ui.TextDisplay("**Total Disc Score**"), accessory=disc_score_button
        )
        container.add_item(disc_score_section)

        container.add_item(disc_media_gallery)

        container.add_item(ui.Separator())

        end_time = time.time()
        process_time = end_time - start_time

        container.add_item(
            ui.TextDisplay(
                f"-# Generated by Yuzubot ･ Character Build by {ctx.author} ･ Took {process_time:.2f}s"
            )
        )

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

    @commands.command()
    async def aet(self, ctx: commands.Context) -> None:
        with open(
            "./jsparsetest/imgs/attribute-physical-icon.a657c07a.png",
            "rb",
        ) as f:
            b = f.read()

        emoji = await self.bot.create_application_emoji(name="test", image=b)
        await ctx.reply(str(emoji))

    @commands.command()
    async def profemoji(self, ctx: Context, id: int) -> None:
        emoji = await self.bot.zzzemoji.get_profession_emoji(id)
        await ctx.reply(str(emoji))


async def setup(bot: Yuzubot):
    await bot.add_cog(BuildCard(bot))
