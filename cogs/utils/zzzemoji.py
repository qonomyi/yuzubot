from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import aiofiles
import aiofiles.os
from discord import Emoji

if TYPE_CHECKING:
    from bot import Yuzubot

log = logging.getLogger(__name__)


class ZZZEmojiHelper:
    def __init__(self, bot: Yuzubot) -> None:
        self.bot = bot
        self.data = {}
        self.emojis = []
        self.emoji_map = {}

        self.zzz_data_path = "./data/zzz/"

    async def emoji_init(self) -> None:
        filter_names = ("attribute", "profession", "prop", "rarity")

        app_emoji_list = await self.bot.fetch_application_emojis()
        existing_emoji = [e.name for e in app_emoji_list]

        imgs_path = self.zzz_data_path + "images/"
        imgs = await aiofiles.os.listdir(imgs_path)

        for filename in imgs:
            name = filename.replace(".png", "")
            name = name.replace("-", "_")

            if not name.startswith(filter_names) or name in existing_emoji:
                continue

            async with aiofiles.open(imgs_path + filename, "rb") as f:
                data = await f.read()
                emoji = await self.bot.create_application_emoji(name=name, image=data)
                log.info(f"Emoji created: {emoji.name} ({emoji.id})")

        self.emojis = await self.bot.fetch_application_emojis()
        self.emoji_map = {e.name: e.id for e in self.emojis}
        log.info("Emoji init done")

    async def data_init(self) -> None:
        ls = await aiofiles.os.listdir(self.zzz_data_path)
        data_files = [i for i in ls if i.endswith("json")]
        for filename in data_files:
            category_name = filename.replace(".json", "")
            async with aiofiles.open(self.zzz_data_path + filename) as f:
                d = json.loads(await f.read())

            self.data[category_name] = d

        log.info("Data init done")
        log.debug(self.data)

    async def get_profession_emoji(self, id: int) -> Emoji | None:
        profession = self.data.get("professions", {}).get(str(id))

        if profession is None:
            return None

        emoji_name = f"profession_{profession}_icon"
        emoji_id = self.emoji_map.get(emoji_name)
        if emoji_id is None:
            return None

        return await self.bot.fetch_application_emoji(emoji_id)

    async def get_element_emoji(
        self, element_id: int, sub_element_id: int = 0
    ) -> Emoji | None:
        element = self.data.get("elements", {}).get(str(element_id))
        sub_element = self.data.get("sub_elements", {}).get(str(sub_element_id))

        if element is None:
            return None

        if sub_element:
            emoji_name = f"attribute_{sub_element}_icon"
        else:
            emoji_name = f"attribute_{element}_icon"

        emoji_id = self.emoji_map.get(emoji_name)
        if emoji_id is None:
            return None

        return await self.bot.fetch_application_emoji(emoji_id)

    async def get_rarity_emoji(self, rarity: str, icon: bool = False) -> Emoji | None:
        emoji_name = f"rarity_{rarity.lower()}{('_icon' if icon else '')}"
        emoji_id = self.emoji_map.get(emoji_name)
        if emoji_id is None:
            return None

        return await self.bot.fetch_application_emoji(emoji_id)
