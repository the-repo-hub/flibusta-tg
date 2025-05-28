import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.types import URLInputFile
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardBuilder

from options import PROXY, BOT_TOKEN, MESSAGE_LIMIT, CAPTION_LIMIT
from flibusta import Flibusta, BookPage
from db import user_db_wrapper

bot = Bot(token=BOT_TOKEN, session=AiohttpSession(proxy=PROXY, timeout=100))
dp = Dispatcher()

def get_download_markup(bookpage: BookPage) -> InlineKeyboardMarkup:
    result = InlineKeyboardBuilder()
    for link in bookpage.links:
        _format = link.split('/')[-1]
        button = InlineKeyboardButton(text=_format, callback_data=link)
        result.add(button)
    return result.as_markup()

@dp.message(CommandStart())
@user_db_wrapper
async def start_handler(msg: Message):
    await msg.reply("Hey! You can just input your search request")

@dp.message(lambda msg: msg.text[:3]=="/b_")
@user_db_wrapper
async def book_handler(msg: Message):
    book_obj = await Flibusta.get_page(msg.text)
    markup = get_download_markup(book_obj)
    text = book_obj.text()
    if book_obj.cover_link:
        try:
            await bot.send_photo(msg.chat.id, photo=f"{Flibusta.url}{book_obj.cover_link}", caption=text[:CAPTION_LIMIT], reply_markup=markup)
        except TelegramBadRequest:
            await bot.send_message(msg.chat.id, text=text[:MESSAGE_LIMIT], reply_markup=markup)
    else:
        await bot.send_message(msg.chat.id, text=text[:MESSAGE_LIMIT], reply_markup=markup)

@dp.message(lambda msg: msg.text[:3]=="/a_")
@user_db_wrapper
async def author_handler(msg: Message):
    author_obj = await Flibusta.get_page(msg.text)
    await msg.reply(text=author_obj.text()[:MESSAGE_LIMIT])

@dp.message()
@user_db_wrapper
async def search_handler(msg: Message):
    print(msg.text)
    result = (await Flibusta.get_search_text(msg.text)).text()
    await msg.reply(result[:MESSAGE_LIMIT])

@dp.callback_query()
async def download_book_handler(call: CallbackQuery):
    full_url = f"{Flibusta.url}{call.data}"
    msg = call.message
    name = msg.html_text.split('\n\n')[0]
    full_name = f"{name}.{call.data.split('/')[-1]}"
    coro = bot.send_document(msg.chat.id, URLInputFile(full_url, filename=full_name))
    await call.answer()
    if msg.caption:
        await bot.edit_message_caption(chat_id=msg.chat.id, message_id=msg.message_id, caption=f"Загружается: {full_name}")
        await coro
        await bot.edit_message_caption(chat_id=msg.chat.id, message_id=msg.message_id, caption=msg.caption,
                                    reply_markup=msg.reply_markup)
    else:
        await bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=f"Загружается: {full_name}")
        await coro
        await bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=msg.text, reply_markup=msg.reply_markup)

async def main() -> None:
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())