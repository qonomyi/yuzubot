import json
import os
import re
import time
from pathlib import Path

import jsfetcher
import jsparser
import requests


def generate_elements(cd: list[str]) -> tuple[dict, dict]:
    elements = {}
    sub_elements = {}

    for p in cd:
        with open("./scripts/cache/" + p, "r", encoding="utf-8") as f:
            content = f.read()

        section = jsparser.find_section_by_variable_val(content, "physical")
        if section is None:
            continue

        alias_map = jsparser.find_alias_map(section)
        r_alias_map = {v: k for k, v in alias_map.items()}

        element_id_map = jsparser.find_id_map_by_value(
            content, "200", r_alias_map["physical"]
        )
        for k, v in element_id_map.items():
            elements[k] = alias_map[v]

        sub_element_id_map = jsparser.find_id_map_by_value(
            content, "1", r_alias_map["frost"]
        )

        for k, v in sub_element_id_map.items():
            sub_elements[k] = alias_map[v]

        break

    return (elements, sub_elements)


def generate_professions(cd: list[str]) -> dict:
    professions = {}
    for p in cd:
        with open("./scripts/cache/" + p, "r", encoding="utf-8") as f:
            content = f.read()

        section = jsparser.find_section_by_variable_val(content, "attack")
        if section is None:
            continue

        alias_map = jsparser.find_alias_map(section)
        r_alias_map = {v: k for k, v in alias_map.items()}

        profession_map = jsparser.find_id_map_by_value(
            content, "1", r_alias_map["attack"]
        )

        for k, v in profession_map.items():
            professions[k] = alias_map[v]

        break

    return professions


def generate_properties(cd: list[str]) -> dict:
    properties = {}
    for p in cd:
        with open("./scripts/cache/" + p, "r", encoding="utf-8") as f:
            content = f.read()

        properties_map = jsparser.find_id_map_by_value(content, "1", "hp")
        if not properties_map:
            continue

        properties = properties_map
        break

    return properties


def generate_skill_types(cd: list[str]) -> dict:
    skill_types = {}
    for p in cd:
        with open("./scripts/cache/" + p, "r", encoding="utf-8") as f:
            content = f.read()

        skill_types_map = jsparser.find_id_map_by_value(content, "0", "normal")
        if not skill_types_map:
            continue

        skill_types = skill_types_map
        break

    return skill_types


def download_images(cd) -> None:
    images_base = "https://act.hoyolab.com/app/zzz-game-record/images/"
    images = []

    for p in cd:
        with open("./scripts/cache/" + p, "r", encoding="utf-8") as f:
            content = f.read()

        result_iter = re.finditer(r"images\/[\w, -]+.\w+?\.png", content)
        result = [r.group().replace("images/", "") for r in result_iter]

        for r in result:
            images.append(r)

    images_set = set(images)

    image_names = {i: re.sub(r"\.[a-f0-9]+(?=\.)", "", i) for i in images_set}

    for orig, name in image_names.items():
        if os.path.exists("./data/zzz/images/" + name):
            print("exists:", name)
            continue
        img = requests.get(images_base + orig).content
        with open("./data/zzz/images/" + name, "wb") as f:
            f.write(img)
            print("downloaded:", name)


#
if __name__ == "__main__":
    zzz_data_path = Path("./data/zzz/images")
    zzz_data_path.mkdir(parents=True, exist_ok=True)

    js_cache_path = Path("./scripts/cache")
    js_cache_path.mkdir(parents=True, exist_ok=True)

    jsfetcher.fetch_all_js()

    cache_list = os.listdir("./scripts/cache")

    elements, sub_elements = generate_elements(cache_list)

    print()

    with open("./data/zzz/elements.json", "w", encoding="utf-8") as f:
        json.dump(elements, f, indent=2, ensure_ascii=False)
        print("elements generated:", elements)

    with open("./data/zzz/sub_elements.json", "w", encoding="utf-8") as f:
        json.dump(sub_elements, f, indent=2, ensure_ascii=False)
        print("sub_elements generated:", sub_elements)

    professions = generate_professions(cache_list)
    with open("./data/zzz/professions.json", "w", encoding="utf-8") as f:
        json.dump(professions, f, indent=2, ensure_ascii=False)
        print("professions generated:", professions)

    properties = generate_properties(cache_list)
    with open("./data/zzz/properties.json", "w", encoding="utf-8") as f:
        json.dump(properties, f, indent=2, ensure_ascii=False)
        print("properties generated:", properties)

    skill_types = generate_skill_types(cache_list)
    with open("./data/zzz/skill_types.json", "w", encoding="utf-8") as f:
        json.dump(skill_types, f, indent=2, ensure_ascii=False)
        print("skill_types generated:", skill_types)

    # print("\nDownload images in 3s")
    # time.sleep(3)

    download_images(cache_list)

    with open("./data/zzz/last_updated.txt", "w", encoding="utf-8") as f:
        f.write(str(int(time.time())))  # Ew.

    print()
    print("Done (●'◡'●)")
