import asyncio
import datetime

import aiohttp
from aiohttp import ClientTimeout


class ProxyChecker:
    def __init__(
            self, session: aiohttp.ClientSession, sem: asyncio.Semaphore, raw_proxies: set
    ):
        self.session = session
        self.sem = sem
        self.raw_proxies = raw_proxies

    async def _get_ip(self):
        try:
            async with self.session.get("https://api.ipify.org") as resp:
                data = await resp.text()
                return data
        except Exception as e:
            return ""

    async def _check_all(self):
        data = await asyncio.gather(
            *[self._check_proxy(i) for i in self.raw_proxies]
        )
        return data

    async def _check_proxy(self, proxy_string):
        try:
            proxy, port = proxy_string.split(":")
        except ValueError:
            return

        resp = {
            "host": proxy,
            "port": port,
            "timeout": "",
            "status_code": 408,
        }

        async with self.sem:
            try:
                start = datetime.datetime.now()
                async with self.session.get(
                        "https://api.ipify.org", proxy=f"http://{proxy}:{port}", timeout=ClientTimeout(5)
                ) as r:

                    response = await r.text()
                    end = datetime.datetime.now()
            except asyncio.exceptions.TimeoutError:
                return resp
            except Exception:
                resp["status_code"] = 520
                return resp

            if r.status != 200:
                return resp

            # if proxy doesn't work correctly
            if response == self.ip:
                resp["status_code"] = 520
                return resp

            return {
                "timeout": round((end - start).total_seconds() * 1000),
                "host": proxy,
                "port": port,
                "status_code": 200,
            }

    async def execute(self):
        self.ip = await self._get_ip()
        result = await self._check_all()
        return result
