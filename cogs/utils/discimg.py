import logging
import os
import pathlib
import time
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

from .types import Disc, DiscProperty

assets_path = "./assets/discimg/"
base_img_path = assets_path + "base.png"
font_path = assets_path + "zzz.ttf"
cache_path = assets_path + "cache/"
fallback_img_path = assets_path + "fallback.png"

log = logging.getLogger(__name__)


def get_disc_icon(disc: Disc) -> str:
    # Returns cached icon path. if cache not found, it downloads from source.
    dp = pathlib.Path(cache_path)
    dp.mkdir(parents=True, exist_ok=True)

    suit_id = str(disc["equip_suit"]["suit_id"])
    if os.path.isfile(cache_path + suit_id + ".png"):
        return cache_path + suit_id + ".png"
    else:
        resp = requests.get(disc["equip_suit"]["icon"])
        if resp.status_code == 200:
            with open(cache_path + suit_id + ".png", "wb") as f:
                f.write(resp.content)
            return cache_path + suit_id + ".png"

    return fallback_img_path


def generate_disc_image(disc: Disc) -> BytesIO:
    start = time.time()

    base_img = Image.open(base_img_path)
    width, height = base_img.size

    draw = ImageDraw.Draw(base_img)

    # Title
    t_font = ImageFont.truetype(font_path, 23.5)
    t_text = disc["name"]
    t_pos = (51.5, 50)
    t_fill = "#F0F0F0"

    draw.text(t_pos, t_text, font=t_font, collor=t_fill)

    # Disc Image
    disc_img = Image.open(get_disc_icon(disc))
    disc_img_r = disc_img.resize((40, 40))
    base_img.paste(disc_img_r, (404, 48), mask=disc_img_r)

    # Mainstats
    mainstat = disc["main_properties"][0]

    is_mainstat_name_long = False
    if len(mainstat["property_name"]) > 8:
        m_font = ImageFont.truetype(font_path, 24)
        is_mainstat_name_long = True
    else:
        m_font = ImageFont.truetype(font_path, 32)

    if mainstat["valid"]:
        m_fill = "#F0F0F0"
    else:
        m_fill = "#808080"

    m_text = mainstat["property_name"]
    if is_mainstat_name_long:
        m_pos = (50, 118 + 4)
    else:
        m_pos = (50, 118)

    draw.text(m_pos, m_text, font=m_font, fill=m_fill, anchor="la")

    m_font = ImageFont.truetype(font_path, 32)

    m_v_text = mainstat["base"]
    m_v_pos = (width - 50, 118)
    draw.text(m_v_pos, m_v_text, font=m_font, fill=m_fill, anchor="ra")

    # Substats & Cache hit count
    hit_count = 0
    max_hit_count = 5
    substats = []

    substats_raw: list[DiscProperty] = disc["properties"]
    for i, s in enumerate(substats_raw):
        if s["valid"]:
            hit_count += s["level"]
            max_hit_count += 1

        name = s["property_name"]
        if s["add"]:
            name += f" (+{s['add']})"

        substats.append([name, s["base"], s["valid"]])

    s_font = ImageFont.truetype(font_path, 24)
    for i, d in enumerate(substats):
        if d[2]:
            s_fill = "#F0F0F0"
        else:
            s_fill = "#808080"

        y = 178 + (38 * i)
        draw.text((50, y), d[0], font=s_font, fill=s_fill, anchor="la")
        draw.text((width - 50, y), d[1], font=s_font, fill=s_fill, anchor="ra")

    # Add mainstat hit count
    if mainstat["valid"]:
        hit_count += 1
        max_hit_count += 1

    # Score
    disc_score = hit_count / max_hit_count * 100
    sc_font = ImageFont.truetype(font_path, 40)
    sc_fill = "#F0F0F0"
    draw.text((50, 401), "Score:", font=sc_font, fill=sc_fill, anchor="la")
    draw.text(
        (width - 50, 401), f"{disc_score:.1f}", font=sc_font, fill=sc_fill, anchor="ra"
    )

    result = BytesIO()
    base_img.save(result, format="PNG")
    result.seek(0)

    end = time.time()
    log.info(f"Disc image generated in {end - start}s")

    return result
