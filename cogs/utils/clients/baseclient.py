import logging

import aiohttp


class HoYoAPIError(Exception):
    def __init__(self, retcode, message):
        self.retcode = retcode
        self.message = message
        super().__init__(f"HoYoLAB API Error {retcode}: {message}")


class BaseClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.log = logging.getLogger(self.__class__.__name__)
        self.session = session

    async def _request(
        self,
        method: str,
        url: str,
        cookies: dict,
        data: dict | None = None,
        return_raw_response: bool = False,
    ) -> dict | aiohttp.ClientResponse:
        headers = {
            "x-rpc-lang": "ja-jp",
            "x-rpc-language": "ja-jp",
            "Accept-Language": "ja",
        }

        resp = await self.session.request(
            method, url, cookies=cookies, json=data, headers=headers
        )

        self.log.info(f"{method} to {url} returned {resp.status}")
        self.log.debug(f"raw: {await resp.text()}")

        if return_raw_response:
            return resp

        async with resp:
            data = await resp.json()
            if data is None:
                raise HoYoAPIError("-999", "Something went wrong")

            retcode = data.get("retcode")
            if retcode != 0:
                raise HoYoAPIError(retcode, data.get("message"))

            return data
