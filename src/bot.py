import asyncio
import gc
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardBuilder
from aiohttp import ClientError

from db import UserMiddleware, init_db
from flibusta import Flibusta, BookPage
from options import BOT_TOKEN, MESSAGE_LIMIT, CAPTION_LIMIT
from options import TELEGRAM_LIMIT_KILOS, TELEGRAM_LIMIT_BYTES, TELEGRAM_LIMIT_MB

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
middleware = UserMiddleware()
dp.update.outer_middleware(middleware)
logger = logging.getLogger("Bot logger")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def get_download_markup(book_page: BookPage) -> InlineKeyboardMarkup:
    result = InlineKeyboardBuilder()
    for link in book_page.links:
        _format = link.split('/')[-1]
        button = InlineKeyboardButton(text=_format, callback_data=link)
        result.add(button)
    return result.as_markup()

@dp.message(CommandStart())
async def start_handler(msg: Message):
    logger.info(f"/start from {msg.from_user.username} with id {msg.from_user.id}")
    await msg.answer("Напиши название книги или фамилию автора.")

@dp.message(lambda msg: msg.text.startswith("/b_"))
async def book_handler(msg: Message):
    book_page = await Flibusta.get_page(msg.text)
    if book_page.name == book_page.doesnt_exist:
        await bot.send_message(
            chat_id=msg.chat.id,
            text=f'Некорректный запрос: такой книги не существует',
        )
        logger.info(f"User {msg.from_user.username} {msg.from_user.id} has requested nonexistent book")
        return
    if book_page.size >= TELEGRAM_LIMIT_KILOS:
        await bot.send_message(
            chat_id=msg.chat.id,
            text=f'Книга слишком большая (больше {TELEGRAM_LIMIT_MB} МБ) и его невозможно передать через Telegram API. Попробуйте найти другую версию книги.',
        )
        logger.info(f"User {msg.from_user.username} {msg.from_user.id} has requested too big book (book_handler_func)")
        return
    markup = get_download_markup(book_page)
    text = book_page.text()
    if book_page.cover_link:
        try:
            await bot.send_photo(msg.chat.id, photo=f"{Flibusta.url}{book_page.cover_link}", caption=text[:CAPTION_LIMIT], reply_markup=markup)
        except TelegramBadRequest:
            await bot.send_message(msg.chat.id, text=text[:MESSAGE_LIMIT], reply_markup=markup)
    else:
        await bot.send_message(msg.chat.id, text=text[:MESSAGE_LIMIT], reply_markup=markup)
    logger.info(f"User {msg.from_user.username} {msg.from_user.id} got his {msg.text} book")

@dp.message(lambda msg: msg.text.startswith("/a_"))
async def author_handler(msg: Message):
    author_obj = await Flibusta.get_page(msg.text)
    if author_obj.name == author_obj.doesnt_exist:
        await bot.send_message(
            chat_id=msg.chat.id,
            text=f'Некорректный запрос: такого автора не существует',
        )
        logger.info(f"User {msg.from_user.username} {msg.from_user.id} has requested nonexistent author")
        return
    await msg.answer(text=author_obj.text()[:MESSAGE_LIMIT])
    logger.info(f"User {msg.from_user.username} {msg.from_user.id} got his {msg.text} author")

@dp.message()
async def search_handler(msg: Message):
    result = (await Flibusta.get_search_text(msg.text)).text()
    await msg.reply(result[:MESSAGE_LIMIT])
    logger.info(f"User {msg.from_user.username} {msg.from_user.id} got his {msg.text} response")

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
    #todo handle it
    try:
        file_as_bytes = await file_b_coro
    #todo im not sure that it is exact exception
    except ClientError:
        await bot.send_message(
            chat_id=msg.chat.id,
            text='Проблема с подключением к флибусте, попробуйте немного позже',
        )
    else:
        if len(file_as_bytes) >= TELEGRAM_LIMIT_BYTES:
            # if flibusta lies
            await bot.send_message(
                chat_id=msg.chat.id,
                text=f'Книга слишком большая (больше {TELEGRAM_LIMIT_MB} МБ) и его невозможно передать через Telegram API. Попробуйте найти другую версию книги.',
            )
            logger.info(f"User {call.from_user.username} {call.from_user.id} has requested too big book (download_handler)")
        else:
            await bot.send_document(msg.chat.id, BufferedInputFile(file_as_bytes, filename=full_name))
            logger.info(f"User {call.from_user.username} {call.from_user.id} got his {full_url} book")
    finally:
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
    table_exists = await init_db()
    if table_exists:
        logger.info("Database table already exists")
    else:
        logger.info("Database table was created")
    await dp.start_polling(bot, loop=loop)

if __name__ == '__main__':
    asyncio.run(main())