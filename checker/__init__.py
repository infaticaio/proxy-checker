import asyncio
import datetime

import aiohttp
from aiohttp import ClientTimeout

IPIFY_URL = "https://api.ipify.org"


class ProxyChecker:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        sem: asyncio.Semaphore,
        raw_proxies: set,
        type_proxy: str,
        check_output: bool,
        target: str,
        readable_timeout: bool,
    ):
        self.session = session
        self.sem = sem
        self.raw_proxies = raw_proxies
        self.type_proxy = type_proxy
        self.check_output = check_output
        self.target = target
        self.readable_timeout = readable_timeout

    async def _get_ip(self):
        try:
            async with self.session.get(IPIFY_URL) as resp:
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

    async def _get(self, scheme, proxy, port, url):
        async with self.session.get(
            url, proxy=f"{scheme}://{proxy}:{port}", timeout=ClientTimeout(5),
        ) as r:
            response = await r.text()
            return response, r.status

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
                "safe": "-",
            }
            async with self.sem:
                try:
                    start = datetime.datetime.now()
                    _, status = await self._get(scheme, proxy, port, self.target)
                    end = datetime.datetime.now()
                except asyncio.exceptions.TimeoutError:
                    collected_resp.append(resp)
                    continue
                except Exception:
                    resp["status_code"] = 520
                    collected_resp.append(resp)
                    continue

                if status != 200:
                    collected_resp.append(resp)
                    continue

                if self.check_output:
                    try:
                        response, _ = await self._get(scheme, proxy, port, IPIFY_URL)
                    except Exception:
                        resp["status_code"] = 520
                        collected_resp.append(resp)
                        continue

                    # if proxy doesn't work correctly
                    if response != self.ip:
                        resp["safe"] = "+"

                readable = 1 if self.readable_timeout else 1000
                resp["timeout"] = round((end - start).total_seconds() * readable)
                resp["status_code"] = 200

                collected_resp.append(resp)

        return collected_resp

    async def execute(self):
        self.ip = await self._get_ip()
        result = await self._check_all()
        return result
