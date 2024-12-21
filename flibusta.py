import re
from typing import Union
from urllib import parse

from bs4 import BeautifulSoup

from base import BaseParser


class InvalidLinkException(Exception):
    pass


class ParseMixin:

    doesnt_exist = "Does not exist"

    @classmethod
    def _convert_link_to_tg(cls, link: str):
        # /b/12121 -> /b_12121
        _, letter, num = link.split('/')
        return f"/{letter}_{num}"


class BookPage(ParseMixin):


    def _process_variables(self, soup: BeautifulSoup):
        _header = soup.find('h1', {'class': 'title'})
        self.name = _header.text
        try:
            self.author_name = _header.find_next_sibling('a').text
        except AttributeError:
            self.name = self.doesnt_exist
            return
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
        _span_size = _div.find('span', {'style': 'size'})
        _links_tags = _span_size.find_next_siblings('a')
        if len(_links_tags) > 1:
            _links_tags = _links_tags[1:]
        self.links = [link.get('href') for link in _links_tags]
        self.num = int(self.links[0].split('/')[2])

    def __init__(self, soup: BeautifulSoup):
        self.name = None
        self.author_name = None
        self.author_link = None
        self.annotation = None
        self.cover_link = None
        self.links = None
        self.num = None
        self._process_variables(soup)

    def text(self) -> str:
        result = f"{self.name}\n\n{self.author_name} {self.author_link}\n\nАннотация:\n\n{self.annotation}"
        return result


class AuthorPage(ParseMixin):

    def _process_variables(self, soup: BeautifulSoup):
        _main = soup.find('div', {'id': 'main'})
        self.name = _main.find('h1', {'class': 'title'}).text
        _form_post = _main.find('form', {'method': "POST"})
        if not _form_post:
            self.name = self.doesnt_exist
            return
        _imgs = _form_post.find_all('img')
        self.books = [tag.find_next_sibling('a') for tag in _imgs]

    def __init__(self, soup: BeautifulSoup):
        self.name = None
        self.books = None
        self._process_variables(soup)

    def text(self) -> str:
        result = f"{self.name}\n\n"
        for num, book in enumerate(self.books, start=1):
            result += f"{num}) {book.text} {self._convert_link_to_tg(book['href'])}\n"
        return result

class SearchPage(ParseMixin):

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


class Flibusta(BaseParser):

    url = "https://flibusta.is"
    pattern = re.compile(r"^/[ab]_\d+$")

    @classmethod
    async def get_search_text(cls, query: str) -> SearchPage:
        url = parse.urljoin(cls.url, f"booksearch?ask={query}&cha=on&chb=on")
        resp = await cls._fetch(url)
        soup = BeautifulSoup(resp, "lxml")
        return SearchPage(soup)

    @classmethod
    async def get_page(cls, link: str) -> Union[BookPage, AuthorPage]:
        # links type /a_1234 or /b_234
        if not cls.pattern.match(link):
            raise InvalidLinkException(f"{link} is not acceptable.")
        letter, num = link.lstrip('/').split('_')
        link = link.replace('_', '/')
        if letter=='a':
            url = parse.urljoin(cls.url, f"{link}?lang=__&order=b&hg1=1&hg=1&sa1=1&hr1=1&hr=1")
            resp = await cls._fetch(url)
            soup = BeautifulSoup(resp,"lxml")
            return AuthorPage(soup)
        elif letter=='b':
            url = parse.urljoin(cls.url, link)
            resp = await cls._fetch(url)
            soup = BeautifulSoup(resp,"lxml")
            return BookPage(soup)
