from bs4 import BeautifulSoup
from urllib import parse
from base import BaseParser

class AnnasArchive(BaseParser):

    url = "https://annas-archive.org"

    @classmethod
    async def search(cls, query: str):
        url = parse.urljoin(cls.url, f"search?q={query}")
        resp = await cls._fetch(url)


# AnnasArchive.search("ISBN 5-691-00644-4")