import aiohttp

from cogs.utils.baseclient import BaseClient


class HoYoAPIError(Exception):
    def __init__(self, retcode, message):
        self.retcode = retcode
        self.message = message
        super().__init__(f"HoYoLab API Error {retcode}: {message}")


class HoYoClient(BaseClient):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__(session)

    async def verify_l_token(self, cookies: dict) -> bool:
        _ = await self._request(
            "POST",
            "https://passport-api-sg.hoyolab.com/account/ma-passport/token/verifyLToken",
            cookies,
        )

        return True

    async def get_game_record_card(self, cookies: dict, hl_uid: str) -> dict:
        data = await self._request(
            "GET",
            "https://bbs-api-os.hoyolab.com/game_record/card/wapi/getGameRecordCard?uid="
            + hl_uid,
            cookies,
        )

        return data
