import json
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command, CommandObject
from parser import Flibusta
import asyncio
import re

options = json.loads(open("options.json").read())
bot = Bot(token=options.get('token'))
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(msg: Message):
    await msg.reply("Hey! You can just input your search request")

@dp.message()
async def get_page_by_link(msg: Message):
    pattern = re.compile(r"^(/[ab])\w*")
    if pattern.match(msg.text):
        result = await Flibusta.get_page(msg.text)
        await msg.reply(result.text())
    else:
        result = await Flibusta.get_search_text(msg.text)
        await msg.reply(result)


async def main() -> None:
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())