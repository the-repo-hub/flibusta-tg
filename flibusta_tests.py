import asyncio
import unittest
from unittest import TestCase

from parameterized import parameterized

from flibusta import Flibusta, BookPage, AuthorPage, SearchPage

books = [
            "/b_531326", "/b_143909", "/b_531366", "/b_179296", "/b_10501", "/b_807198", "/b_178074", "/b_10500",
             "/b_169388", "/b_169373", "/b_169387", "/b_169412", "/b_169357", "/b_169368", "/b_339196", "/b_531372",
             "/b_531373", "/b_169502", "/b_169337", "/b_636443", "/b_169343", "/b_169473", "/b_10524", "/b_531375",
             "/b_244150", "/b_169347", "/b_531374", "/b_638080", "/b_169372", "/b_415171", "/b_10514", "/b_169394",
             "/b_82076", "/b_82073", "/b_757729", "/b_493844", "/b_424966", "/b_647643", "/b_10526", "/b_82081",
             "/b_82079", "/b_167891", "/b_638669", "/b_10727", "/b_659063", "/b_727674", "/b_723104", "/b_337710",
             "/b_435515", "/b_708495", "/b_169447", "/b_169458", "/b_601915", "/b_82101", "/b_124471", "/b_535957",
             "/b_692321", "/b_734789", "/b_690376", "/b_707467", "/b_10733", "/b_367899", "/b_169466", "/b_169367",
             "/b_531400", "/b_169356", "/b_531403", "/b_143910", "/b_169441", "/b_703532", "/b_169454", "/b_10741",
             "/b_169451", "/b_169355", "/b_531381", "/b_531383", "/b_10726", "/b_531389", "/b_602186", "/b_604198",
             "/b_169359", "/b_604205", "/b_531394", "/b_169265", "/b_234760", "/b_367898", "/b_169406", "/b_602286",
             "/b_531397", "/b_169376", "/b_604920", "/b_169477", "/b_169363", "/b_169415", "/b_395619", "/b_169369",
             "/b_601908", "/b_531404", "/b_10560", "/b_10559", "/b_234756", "/b_378978", "/b_10561", "/b_10562",
             "/b_168419", "/b_801351", "/b_447416", "/b_531406", "/b_143911", "/b_473583", "/b_10534", "/b_10553",
             "/b_531407", "/b_531408", "/b_82090", "/b_82089", "/b_601904", "/b_367891", "/b_10539", "/b_580736",
             "/b_169409", "/b_143912", "/b_601973", "/b_82086", "/b_169442", "/b_169253", "/b_169450", "/b_169375",
             "/b_447429", "/b_801154", "/b_531409", "/b_10545", "/b_16934", "/b_447430"
         ]

authors = [
    '/a_303633', '/a_309182', '/a_217114', '/a_19245', '/a_267612', '/a_244522', '/a_229269', '/a_302205', '/a_310410', '/a_309803', '/a_264599', '/a_216090', '/a_157498', '/a_233764', '/a_301905', '/a_157503', '/a_92925', '/a_120423', '/a_124027', '/a_302870', '/a_253672', '/a_309184', '/a_230899', '/a_268646', '/a_189655', '/a_103654', '/a_12417', '/a_220773', '/a_198361', '/a_220751', '/a_306657', '/a_157504', '/a_273247', '/a_276466', '/a_162014', '/a_117538', '/a_236972', '/a_84483', '/a_112455', '/a_128763', '/a_245055', '/a_220699', '/a_220700', '/a_95031', '/a_220841', '/a_126418', '/a_250586', '/a_96806', '/a_266944', '/a_220914', '/a_238397', '/a_237106', '/a_99506', '/a_89518', '/a_236970', '/a_152764', '/a_220913', '/a_254416', '/a_33691', '/a_144593', '/a_220774', '/a_49547', '/a_238906', '/a_11010', '/a_157555', '/a_19243', '/a_262496', '/a_238186', '/a_104427', '/a_174391', '/a_302077', '/a_92642', '/a_160013', '/a_120262', '/a_298351', '/a_274522', '/a_98211', '/a_122119', '/a_226090', '/a_260343', '/a_55142', '/a_149452', '/a_281564', '/a_55553', '/a_235300', '/a_304459', '/a_96060', '/a_32907', '/a_136398', '/a_241214', '/a_220765', '/a_219675', '/a_207116', '/a_254703', '/a_189935', '/a_220101', '/a_61316', '/a_273136', '/a_55515', '/a_242789']

non_existent_books = [
    "/b_4474313",
    "/b_8013513",
    "/b_53140613",
]

non_existent_authors = [
    "/a_3036234322323433",
    "/a_309342342334182",
    "/a_217113422432344",
]

async def get_pages():
    books_tasks = []
    authors_tasks = []
    nonexistent_books_tasks = []
    nonexistent_authors_tasks = []
    loop = asyncio.get_event_loop()
    for link in books:
        books_tasks.append(loop.create_task(Flibusta.get_page(link)))
    for link in authors:
        authors_tasks.append(loop.create_task(Flibusta.get_page(link)))
    for link in non_existent_books:
        nonexistent_books_tasks.append(loop.create_task(Flibusta.get_page(link)))
    for link in non_existent_authors:
        nonexistent_authors_tasks.append(loop.create_task(Flibusta.get_page(link)))
    books_tasks = await asyncio.gather(*books_tasks)
    authors_tasks = await asyncio.gather(*authors_tasks)
    nonexistent_books_tasks = await asyncio.gather(*nonexistent_books_tasks)
    nonexistent_authors_tasks = await asyncio.gather(*nonexistent_authors_tasks)
    return books_tasks, authors_tasks, nonexistent_books_tasks, nonexistent_authors_tasks

async def get_search_pages():
    query = "Чехов"
    query_non_exist = "jsfksfjkdjkf"

    return await asyncio.gather(
        Flibusta.get_search_text(query),
        Flibusta.get_search_text(query_non_exist)
    )

class ParserTests(TestCase):

    book_pages, authors_pages, nonexistent_books_pages, nonexistent_authors_pages = asyncio.run(get_pages())
    search_page, search_page_non_exist = asyncio.run(get_search_pages())


    @parameterized.expand([(page,) for page in book_pages])
    def test_book_page(self, book_page: BookPage):
        print(book_page.name, book_page.links)
        book_page.text()
        self.assertTrue(book_page.name)
        self.assertTrue(book_page.author_name)
        self.assertTrue(book_page.author_link)
        self.assertTrue(book_page.links)
        self.assertTrue(book_page.num)
        self.assertIsInstance(book_page.num, int)

    @parameterized.expand([(page,) for page in authors_pages])
    def test_author_page(self, author_page: AuthorPage):
        print(author_page.name)
        author_page.text()
        self.assertTrue(author_page.name)
        self.assertTrue(author_page.books)

    @parameterized.expand([(page,) for page in nonexistent_books_pages])
    def test_nonexistent_book_pages(self, book_page: BookPage):
        self.assertEqual(book_page.name, BookPage.doesnt_exist)
        self.assertFalse(book_page.author_name)
        self.assertFalse(book_page.author_link)
        self.assertFalse(book_page.links)
        self.assertFalse(book_page.num)

    @parameterized.expand([(page,) for page in nonexistent_authors_pages])
    def test_nonexistent_author_pages(self, author_page: AuthorPage):
        self.assertEqual(author_page.name, AuthorPage.doesnt_exist)
        self.assertFalse(author_page.books)

    def test_search_pages(self):
        self.assertTrue(self.search_page.dict)
        self.search_page.text()

    def test_search_page_non_exist(self):
        self.assertFalse(self.search_page_non_exist.dict)

if __name__ == '__main__':
    unittest.main()