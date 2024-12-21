from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
import fake_useragent

class BaseParser:

    proxy = "socks5://localhost:9050"
    headers = {
        "User-Agent": fake_useragent.FakeUserAgent().firefox
    }

    @classmethod
    async def _fetch(cls, url):
        connector = ProxyConnector.from_url(cls.proxy, rdns=True)
        async with ClientSession(headers=cls.headers, connector=connector) as session:
            response = await session.get(url)
            return await response.read()