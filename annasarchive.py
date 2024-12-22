from bs4 import BeautifulSoup, Tag
from urllib import parse
from base import BaseParser

class AnnasBook:

    def __init__(self, _link: Tag):
        self.url = _link.get('href')
        _h3 = _link.find('h3')
        self.name = _h3.text
        _bibl = _h3.find_next_sibling('div')
        self.bibliography = _bibl.text
        self.author = _bibl.find_next_sibling('div').text


class AnnasSearchPage:

    def _process_vars(self, soup):
        _form = soup.find('form', attrs={'action': '/search'})
        _results_div = _form.find('div', attrs={'class': 'mb-4'})
        _links = _results_div.find_all('a')
        self.books = [AnnasBook(link) for link in _links]

    def __init__(self, soup: BeautifulSoup):
        self.books = None
        self._process_vars(soup)

class AnnasArchive(BaseParser):

    url = "https://annas-archive.org"

    @classmethod
    async def search(cls, query: str):
        url = parse.urljoin(cls.url, f"search?q={query}")
        resp = await cls._fetch(url)
        soup = BeautifulSoup(resp.decode(), "lxml")
        return AnnasSearchPage(soup)
