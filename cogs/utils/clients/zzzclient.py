from typing import cast

import aiohttp

from .baseclient import BaseClient


class ZZZClient(BaseClient):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session
        super().__init__(self.session)

    async def get_game_record(self, cookies: dict):
        data = await self._request(
            "GET",
            "https://bbs-api-os.hoyolab.com/game_record/card/wapi/getGameRecordCard?uid="
            + cookies["account_id_v2"],
            cookies,
        )

        data = cast(dict, data)
        zzz_data = next((i for i in data["data"]["list"] if i["game_id"] == 8), None)

        return zzz_data or {}

    async def get_e_nap_token(self, cookies: dict, zzz_uid: str) -> str:
        nap_data = {
            "game_biz": "nap_global",
            "lang": "ja-jp",
            "region": "prod_gf_jp",
            "uid": zzz_uid,
        }

        resp = await self._request(
            "POST",
            "https://sg-public-api.hoyolab.com/common/badge/v1/login/account",
            cookies,
            nap_data,
            return_raw_response=True,
        )

        async with cast(aiohttp.ClientResponse, resp) as resp:
            resp_cookies = resp.cookies

        return resp_cookies["e_nap_token"].value or ""

    async def get_owned_agent_list(self, cookies: dict, zzz_uid: int) -> list:
        data = await self._request(
            "GET",
            "https://sg-public-api.hoyolab.com/event/game_record_zzz/api/zzz/avatar/basic?server=prod_gf_jp&role_id="
            + str(zzz_uid),
            cookies,
        )
        data = cast(dict, data)

        return data["data"].get("avatar_list") or []

    async def get_agent_detail(
        self, cookies: dict, zzz_uid: str, agent_id: int
    ) -> dict:
        data = {"avatar_list": [{"avatar_id": agent_id}]}

        detail = await self._request(
            "POST",
            "https://sg-public-api.hoyolab.com/event/nap_cultivate_tool/user/batch_avatar_detail_v2?region=prod_gf_jp&uid="
            + str(zzz_uid),
            cookies,
            data,
        )
        detail = cast(dict, detail)

        return detail
