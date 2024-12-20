from typing import Union

import aiohttp
import fake_useragent
from bs4 import BeautifulSoup


class InvalidLinkException(Exception):
    pass

class BaseMixin:

    url = "https://flibusta.is"
    headers = {
        "User-Agent": fake_useragent.FakeUserAgent().firefox
    }

    @classmethod
    def _convert_link_to_tg(cls, link: str):
        # /b/12121 -> /b_12121
        _, letter, num = link.split('/')
        return f"/{letter}_{num}"

class BookPage(BaseMixin):

    def __init__(self, soup: BeautifulSoup):
        _header = soup.find('h1', {'class': 'title'})
        self.name = _header.text
        self.author = _header.find_next_sibling('a').text
        self.author_link = self._convert_link_to_tg(_header.find_next_sibling('a').get('href'))
        try:
            self.annotation = _header.find_next_sibling('p').text
        except AttributeError:
            self.annotation = "Отсутствует."
        try:
            self.cover_link = f"{self.url}{_header.find_next_sibling('img').get('src')}"
        except AttributeError:
            self.cover_link = None
        _div = _header.find_next_sibling('div')
        _span_size = _div.find('span', {'style': 'size'})
        _links_tags = _span_size.find_next_siblings('a')
        if len(_links_tags) > 1:
            _links_tags = _links_tags[1:]
        self.links = [link.get('href') for link in _links_tags]
        self.num = int(self.links[0].split('/')[2])

    def text(self) -> str:
        result = f"{self.name}\n\n{self.author} {self.author_link}\n\nАннотация:\n\n{self.annotation}"
        return result


class AuthorPage(BaseMixin):

    def __init__(self, soup: BeautifulSoup):
        _main = soup.find('div', {'id': 'main'})
        self.author = _main.find('h1').text
        _form_post = _main.find('form', {'method': "POST"})
        _imgs = _form_post.find_all('img')
        self.books = [tag.find_next_sibling('a') for tag in _imgs]

    def text(self) -> str:
        result = f"{self.author}\n\n"
        for num, book in enumerate(self.books, start=1):
            result += f"{num}) {book.text} {self._convert_link_to_tg(book['href'])}\n"
        return result

class SearchPage(BaseMixin):

    def __init__(self, soup: BeautifulSoup):
        _headers = soup.find_all('h3')
        self.dict = {}
        for h3 in _headers:
            lines = h3.find_next_sibling('ul').find_all('li')
            header = h3.text.strip()
            self.dict[header] = []
            for li in lines:
                a = li.find('a')
                self.dict[header].append(f"{a.text} {self._convert_link_to_tg(a.get('href'))}")

    def text(self) -> str:
        result = str()
        if not self.dict:
            return "Ничего не найдено. Введите фамилию автора или название книги для поиска."
        for key in self.dict.keys():
            result += f"{key}\n\n"
            for num, value in enumerate(self.dict[key], start=1):
                result += f"{num}) {value}\n"
            result += "\n"
        return result



class Flibusta(BaseMixin):


    @classmethod
    async def get_search_text(cls, query: str) -> SearchPage:
        async with aiohttp.ClientSession(headers=cls.headers) as session:
            resp = await session.get(f"{cls.url}/booksearch?ask={query}&cha=on&chb=on")
            soup = BeautifulSoup(await resp.read(), "html.parser")
        return SearchPage(soup)

    @classmethod
    async def get_page(cls, link: str) -> Union[BookPage, AuthorPage]:
        # links type /a_1234 or /b_234
        letter, num = link.lstrip('/').split('_')
        link = link.replace('_', '/')
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
