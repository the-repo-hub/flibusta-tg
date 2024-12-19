import asyncio
import json

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.types import URLInputFile
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardBuilder

from parser import Flibusta, BookPage

options = json.loads(open("options.json").read())
bot = Bot(token=options.get('token'))
dp = Dispatcher()

def get_download_markup(bookpage: BookPage) -> InlineKeyboardMarkup:
    result = InlineKeyboardBuilder()
    for link in bookpage.links:
        _format = link.split('/')[-1]
        button = InlineKeyboardButton(text=_format, callback_data=link)
        result.add(button)
    return result.as_markup()


@dp.message(CommandStart())
async def start_handler(msg: Message):
    await msg.reply("Hey! You can just input your search request")

@dp.message(lambda msg: msg.text[:3]=="/b_")
async def book_handler(msg: Message):
    book_obj = await Flibusta.get_page(msg.text)
    markup = get_download_markup(book_obj)
    if book_obj.cover_link:
        await bot.send_photo(msg.chat.id, photo=book_obj.cover_link, caption=book_obj.text(), reply_markup=markup)
    else:
        await bot.send_message(msg.chat.id, text=book_obj.text(), reply_markup=markup)

@dp.message(lambda msg: msg.text[:3]=="/a_")
async def author_handler(msg: Message):
    author_obj = await Flibusta.get_page(msg.text)
    await msg.reply(text=author_obj.text())

@dp.message()
async def search_handler(msg: Message):
    result = (await Flibusta.get_search_text(msg.text)).text()[:4096]
    await msg.reply(result)

@dp.callback_query()
async def download_book_handler(call: CallbackQuery):
    full_url = f"{Flibusta.url}{call.data}"
    name = call.message.html_text.split('\n\n')[0]
    full_name = f"{name}.{call.data.split('/')[-1]}"
    await bot.send_document(call.message.chat.id, URLInputFile(full_url, filename=full_name))
    await call.answer()

async def main() -> None:
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())