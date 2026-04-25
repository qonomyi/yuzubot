import re
import os

import requests

base = "https://act.hoyolab.com/app/zzz-game-record/"

js_in_html_pattern = r"pc_\w+\.js"
js_in_init_js_pattern = r'\{1:"?\w{8,8}"?(,?\w+:"?\w{8,8}"?)+\}'


def fetch_all_js():
    raw_html = requests.get(
        "https://act.hoyolab.com/app/zzz-game-record/index.html"
    ).text

    # fetch the initial js that contains other js filenames
    # (and parse filenames)
    it = re.finditer(js_in_html_pattern, raw_html)
    js_ids = []

    for i in it:
        print("fetching:", i.group())
        data = requests.get(base + i.group()).text
        with open("./scripts/cache/" + i.group(), "w", encoding="utf-8") as f:
            f.write(data)

        r = None

        try:
            r = re.finditer(js_in_init_js_pattern, data)
            id_match = [i.group() for i in r][-1]
            p = re.findall(r'(\w+):"?(\w+)"?', id_match)

            js_ids = [v for _, v in p]
        except Exception:
            continue

    print("parsed:", js_ids)

    for id in js_ids:
        name = f"pc_{id}.js"
        if os.path.exists("./scripts/cache/" + name):
            print("exists:", name)
            continue

        data = requests.get(base + name).text
        print("fetching:", name)
        with open("./scripts/cache/" + name, "w", encoding="utf-8") as f:
            f.write(data)
