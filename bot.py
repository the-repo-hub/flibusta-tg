import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, CommandObject
from parser import Flibusta, BookPage, AuthorPage
import asyncio
import re
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardBuilder

options = json.loads(open("options.json").read())
bot = Bot(token=options.get('token'))
dp = Dispatcher()

def get_download_markup(bookpage: BookPage) -> InlineKeyboardMarkup:
    result = InlineKeyboardBuilder()
    for link in bookpage.links:
        name = link.split('/')[-1]
        button = InlineKeyboardButton(text=name, callback_data=f"{bookpage.url}{link}")
        result.add(button)
    return result.as_markup()

@dp.message(CommandStart())
async def start_handler(msg: Message):
    await msg.reply("Hey! You can just input your search request")

@dp.message()
async def get_page_by_link(msg: Message):
    pattern = re.compile(r"^(/[ab])\w*")
    if pattern.match(msg.text):
        page_obj = await Flibusta.get_page(msg.text)
        markup = get_download_markup(page_obj)
        if isinstance(page_obj, BookPage) and page_obj.cover_link:
            await bot.send_photo(msg.chat.id, photo=page_obj.cover_link, caption=page_obj.text(), reply_markup=markup)
        else:
            await bot.send_message(msg.chat.id, text=page_obj.text(), reply_markup=markup)
    else:
        result = (await Flibusta.get_search_text(msg.text)).text()[:4096]
        await msg.reply(result)

@dp.callback_query()
async def download_book_handler(call: CallbackQuery):
    await call.answer()

async def main() -> None:
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())