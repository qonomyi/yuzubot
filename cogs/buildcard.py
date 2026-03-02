from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import TYPE_CHECKING

import discord
from discord import Interaction, app_commands, ui
from discord.ext import commands
from discord.ext.commands import Context

from .utils import discimg
from .utils.types import Disc, DiscProperty, HoYoUserData

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from bot import Yuzubot


class BuildCard(commands.Cog):
    def __init__(self, bot: Yuzubot) -> None:
        self.bot: Yuzubot = bot
        self.owned_cache: dict[str, dict] = {}

    def none_empty_discs(self, discs: list[Disc | None]) -> list[Disc | None]:
        result: list[Disc | None] = [None] * 6
        for disc in discs:
            try:
                if not disc:
                    continue

                # パファー・エレクトロ[1] から数字部分を取得
                num = int(disc["name"][-2])
                idx = num - 1

                if 0 <= idx < 6:
                    result[idx] = disc
            except (ValueError, IndexError):
                continue
        return result

    async def buildcard_get_owned(self, user_id: int) -> dict:
        if c := self.owned_cache.get(str(user_id)):
            return c
        else:
            creds: HoYoUserData | None = await self.bot.hoyolab_creds.get_zzz(user_id)
            if creds is None:
                return {}
            owned = await self.bot.zzzclient.get_owned_agent_list(
                creds["cookies"], creds["zzz_uid"]
            )
            self.owned_cache[str(user_id)] = {
                a["full_name_mi18n"]: a["id"] for a in owned
            }

            return self.owned_cache.get(str(user_id)) or {}

    async def agent_id_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[int]]:
        assert interaction.user.id is not None
        owned = await self.buildcard_get_owned(interaction.user.id)
        return [
            app_commands.Choice(name=name, value=agent_id)
            for name, agent_id in owned.items()
            if current.lower() in name.lower()
        ][:25]

    @commands.hybrid_command()
    @app_commands.autocomplete(agent_id=agent_id_autocomplete)
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

        rarity_icon_emoji = (
            await self.bot.zzzemoji.get_rarity_emoji(
                agent["avatar"]["rarity"], icon=True
            )
            or ""
        )

        element_emoji = (
            await self.bot.zzzemoji.get_element_emoji(
                agent["avatar"]["element_type"], agent["avatar"]["sub_element_type"]
            )
            or ""
        )

        profession_emoji = (
            await self.bot.zzzemoji.get_profession_emoji(
                agent["avatar"]["avatar_profession"]
            )
            or ""
        )

        has_awaken = agent["avatar"]["skill_awaken"]["has_awaken_system"]
        awaken_level = 0

        awaken_text = ""
        if has_awaken:
            awaken_level = agent["avatar"]["skill_awaken"]["awaken_level"]
            awaken_text += f" ･ Potential {awaken_level}"

        # Main Stats
        main_text_raw = (
            f"# {rarity_icon_emoji} {agent['avatar']['name_mi18n']} {element_emoji}{profession_emoji}\n"
            + f"-# Lvl {agent['avatar']['level']} ･ Mindscape {agent['avatar']['rank']}{awaken_text}\n"
        )

        stats_text = ""
        for i, p in enumerate(agent["avatar"]["properties"]):
            prop_name = p["property_name"]
            prop_emoji = await self.bot.zzzemoji.get_prop_emoji(p["property_id"]) or ""

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
            we_rarity_emoji = (
                await self.bot.zzzemoji.get_rarity_emoji(we["rarity"], icon=False) or ""
            )

            we_name = we["name"]
            we_prop = we["properties"][0]
            we_sub_prop = we["main_properties"][0]
            we_talent_content = re.sub(r"<\/?(\w|=|#)+>", "", we["talent_content"])
            we_text_raw = (
                f"## {we_rarity_emoji} {we_name}\n"
                + f"-# Lvl {we['level']} ･ Phase {we['star']}\n"
                + f"> {we_prop['property_name']}: {we_prop['base']} ･ "
                + f"{we_sub_prop['property_name']}: {we_sub_prop['base']}\n"
                + f"> -# {we_talent_content}"
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
            skill_emoji = (
                await self.bot.zzzemoji.get_skill_emoji(skill["skill_type"]) or ""
            )

            skills_text_raw += f"{skill_emoji} {skill['level']} | "

        skills_text_raw = skills_text_raw[:-2]
        skills_text = ui.TextDisplay(skills_text_raw)
        container.add_item(skills_text)
        container.add_item(ui.Separator())

        # Disc
        disc_media_gallery = ui.MediaGallery()
        files = []

        discs: list[Disc | None] = agent["equip"]
        if len(discs) < 6:
            discs = self.none_empty_discs(discs)

        total_disc_score = 0.0

        for i, disc in enumerate(discs):
            if disc is None:
                log.info("Disc is None, adding fallback")

                file = discord.File("./assets/discimg/fallback.png", f"fallback{i}.png")
                files.append(file)

                disc_media_gallery.add_item(media=file)
                continue

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


async def setup(bot: Yuzubot):
    await bot.add_cog(BuildCard(bot))
