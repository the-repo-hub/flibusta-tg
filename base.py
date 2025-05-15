import fake_useragent
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector


class BaseRequest:

    url = "http://flibusta.is"
    proxy = "http://192.168.1.124:10808"
    headers = {
        "User-Agent": fake_useragent.FakeUserAgent().firefox
    }

    @classmethod
    async def _fetch(cls, url) -> bytes:
        connector = ProxyConnector.from_url(cls.proxy, rdns=True)
        async with ClientSession(headers=cls.headers, connector=connector) as session:
            response = await session.get(url)
            return await response.read()