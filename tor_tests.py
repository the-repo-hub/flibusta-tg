import unittest
from unittest import TestCase
from stem.control import Controller
import json
import asyncio
from flibusta import Flibusta
from aiohttp import ClientSession

class TestTor(TestCase):

    @staticmethod
    async def _no_tor_fetch(url: str):
        async with ClientSession(headers=Flibusta.headers) as session:
            response = await session.get(url)
            return await response.read()

    async def _fetch_both(self, url: str):
        return await asyncio.gather(self._no_tor_fetch(url), Flibusta._fetch(url))

    def test_tor_service_status(self):
        with Controller.from_port(port=9051) as controller:
            with open('options.json') as f:
                password = json.loads(f.read())['tor_password']
            controller.authenticate(password=password)
            status = controller.get_info("status/circuit-established")
            self.assertEqual(status, '1')

    def test_parser_tor_connection(self):
        url = "https://httpbin.org/ip"
        no_tor, tor = asyncio.run(self._fetch_both(url))
        no_tor, tor = json.loads(no_tor)['origin'], json.loads(tor)['origin']
        self.assertNotEqual(no_tor, tor)


if __name__ == '__main__':
    unittest.main()