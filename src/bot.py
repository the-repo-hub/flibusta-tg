import asyncio
import gc
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardBuilder

from db import user_db_wrapper
from flibusta import Flibusta, BookPage
from options import BOT_TOKEN, MESSAGE_LIMIT, CAPTION_LIMIT
from options import TELEGRAM_LIMIT

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logger = logging.getLogger("Bot logger")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

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
    logger.info(f"/start from {msg.from_user.username} with id {msg.from_user.id}")
    await msg.answer("Напиши название книги или фамилию автора.")

@dp.message(lambda msg: msg.text[:3]=="/b_")
@user_db_wrapper
async def book_handler(msg: Message):
    book_obj = await Flibusta.get_page(msg.text)
    if book_obj.size >= TELEGRAM_LIMIT:
        await bot.send_message(
            chat_id=msg.chat.id,
            text=f'Книга слишком большая (больше 50 МБ) и его невозможно передать через Telegram API. Попробуйте найти другую версию книги.')
        return
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
    await msg.answer(text=author_obj.text()[:MESSAGE_LIMIT])

@dp.message()
@user_db_wrapper
async def search_handler(msg: Message):
    logger.info(f"Search query {msg.text} from {msg.from_user.username} with id {msg.from_user.id}")
    result = (await Flibusta.get_search_text(msg.text)).text()
    await msg.reply(result[:MESSAGE_LIMIT])

async def message_or_caption_editor(msg:Message, text: str, markup=None) -> str:
    if msg.caption:
        await bot.edit_message_caption(chat_id=msg.chat.id, message_id=msg.message_id, caption=text, reply_markup=markup)
        return msg.caption
    else:
        await bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id, text=text, reply_markup=markup)
        return msg.text

@dp.callback_query()
async def download_book_handler(call: CallbackQuery):
    full_url = f"{Flibusta.url}{call.data}"
    msg = call.message
    name = msg.html_text.split('\n\n')[0]
    full_name = f"{name}.{call.data.split('/')[-1]}"
    file_b_coro = Flibusta.async_fetch(full_url)
    logger.info(f"User {call.from_user.username} with id {call.from_user.id} is downloading {full_name} from {full_url}")
    old_text = await message_or_caption_editor(msg, f"Загружается: {full_name}")
    await call.answer()
    file_as_bytes = await file_b_coro
    await bot.send_document(msg.chat.id, BufferedInputFile(file_as_bytes, filename=full_name))
    await message_or_caption_editor(msg, old_text, msg.reply_markup)

async def gc_handler():
    logger.info(f"Garbage collector started")
    while True:
        await asyncio.sleep(3600)
        gc.collect()
        logger.info("Garbage collector has worked")

async def main() -> None:
    loop = asyncio.get_event_loop()
    loop.create_task(gc_handler())
    await dp.start_polling(bot, loop=loop)

if __name__ == '__main__':
    asyncio.run(main())