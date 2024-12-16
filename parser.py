import asyncio

import aiohttp
import fake_useragent
from bs4 import BeautifulSoup
from typing import Union

class InvalidLinkException(Exception):
    pass

class BaseMixin:

    @classmethod
    def _convert_link_to_tg(cls, link: str):
        # /b/12121 -> /b-12121
        _, letter, num = link.split('/')
        return f"/{letter}-{num}"

class BookPage(BaseMixin):

    def __init__(self, soup: BeautifulSoup):
        _header = soup.find('h1', {'class': 'title'})
        self.header = _header.text
        self.author = _header.find_next_sibling('a').text
        self.author_link = self._convert_link_to_tg(_header.find_next_sibling('a').get('href'))
        try:
            self.annotation = _header.find_next_sibling('p').text
        except AttributeError:
            self.annotation = "Отсутствует."
        try:
            self.cover_link = _header.find_next_sibling('img').get('src')
        except AttributeError:
            self.cover_link = None
        _div = _header.find_next_sibling('div')
        _span_size = _div.find('span')
        self.formats = list(map(lambda tag: tag.get('href').split('/')[-1], _span_size.find_next_siblings('a')[1:]))

    def text(self) -> str:
        result = f"{self.header}\n\n{self.author} {self.author_link}\n\nАннотация:\n\n{self.annotation}"
        return result

class AuthorPage(BaseMixin):

    def __init__(self, soup: BeautifulSoup):
        _main = soup.find('div', {'id': 'main'})
        self.author = _main.find('h1').text
        _form_post = _main.find('form', {'method': "POST"})
        _inputs = _form_post.find_all('input', {'type': "checkbox"})
        self.books = [tag.find_next_sibling('a') for tag in _inputs]

    def text(self) -> str:
        result = f"{self.author}\n\n"
        for book in self.books:
            result += f"{book.text} {self._convert_link_to_tg(book['href'])}\n"
        return result


class Flibusta(BaseMixin):

    url = "https://flibusta.is"
    headers = {
        "User-Agent": fake_useragent.FakeUserAgent().firefox
    }

    @classmethod
    async def get_search_text(cls, query: str) -> str:
        async with aiohttp.ClientSession(headers=cls.headers) as session:
            resp = await session.get(f"{cls.url}/booksearch?ask={query}")
            soup = BeautifulSoup(await resp.read())
        headers = soup.find_all('h3')
        result = ""
        for h3 in headers:
            result += f"{h3.text.strip()}\n\n"
            lines = h3.find_next_sibling('ul').find_all('li')
            for line in lines:
                link = line.find('a')['href']
                result += f"{line.text} {link}\n"
        return result

    @classmethod
    async def get_page(cls, link: str) -> Union[BookPage, AuthorPage]:
        # links type a-1234 or b-1234
        letter, num = link.split('-')
        link = link.replace('-', '/')
        async with aiohttp.ClientSession(headers=cls.headers) as session:
            if letter=='a':
                resp = await session.get(f"{cls.url}/{link}?lang=__&order=a&hg1=1&sa1=1&hr1=1")
                soup = BeautifulSoup(await resp.read(),"html.parser")
                return AuthorPage(soup)
            elif letter=='b':
                resp = await session.get(f"{cls.url}/{link}")
                soup = BeautifulSoup(await resp.read(),"html.parser")
                return BookPage(soup)
        raise InvalidLinkException(f"{link} and its letter {letter} is not acceptable.")

# async def main():
#     # page = await Flibusta.get_page("a-2755")
#     page = await Flibusta.get_page("b-1488")
#     page = await Flibusta.get_page("b-441")
#     page = await Flibusta.get_page("b-771")
#     print(page.text())
#
# asyncio.run(main())
