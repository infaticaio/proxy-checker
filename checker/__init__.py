import asyncio
import datetime

import aiohttp
from aiohttp import ClientTimeout


class ProxyChecker:
    def __init__(
            self, session: aiohttp.ClientSession, sem: asyncio.Semaphore, raw_proxies: set, type_proxy: str
    ):
        self.session = session
        self.sem = sem
        self.raw_proxies = raw_proxies
        self.type_proxy = type_proxy

    async def _get_ip(self):
        try:
            async with self.session.get("https://api.ipify.org") as resp:
                data = await resp.text()
                return data
        except Exception as e:
            return ""

    async def _check_all(self):
        data = []
        for i in await asyncio.gather(
                *[self._check_proxy(i) for i in self.raw_proxies]
        ):
            if i:
                data.extend(i)

        return data

    async def _check_proxy(self, proxy_string):
        try:
            proxy, port = proxy_string.split(":")
        except ValueError:
            return

        collected_resp = []

        for scheme in [self.type_proxy]:
            resp = {
                "host": proxy,
                "port": port,
                "timeout": "",
                "status_code": 408,
                "scheme": scheme,
            }
            async with self.sem:
                try:
                    start = datetime.datetime.now()
                    async with self.session.get(
                            "https://api.ipify.org",
                            proxy=f"{scheme}://{proxy}:{port}",
                            timeout=ClientTimeout(30),
                    ) as r:

                        response = await r.text()
                        end = datetime.datetime.now()
                except asyncio.exceptions.TimeoutError:
                    collected_resp.append(resp)
                    continue
                except Exception:
                    resp["status_code"] = 520
                    collected_resp.append(resp)
                    continue

                if r.status != 200:
                    collected_resp.append(resp)
                    continue

                resp["timeout"] = round((end - start).total_seconds() * 1000)
                resp["status_code"] = 200

                collected_resp.append(resp)

        return collected_resp

    async def execute(self):
        self.ip = await self._get_ip()
        result = await self._check_all()
        return result
