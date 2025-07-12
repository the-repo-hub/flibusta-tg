import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ['BOT_TOKEN']
if not BOT_TOKEN:
    raise ValueError('Missing token')
PROXY = os.environ['PROXY']
if not PROXY:
    raise ValueError('Missing proxy')
DATABASE_URL = os.environ['DATABASE_URL']
if not DATABASE_URL:
    raise ValueError('Missing database url')
MESSAGE_LIMIT = 4096
CAPTION_LIMIT = 1024
TELEGRAM_LIMIT_MB = 50
TELEGRAM_LIMIT_KILOS = TELEGRAM_LIMIT_MB * 1024
TELEGRAM_LIMIT_BYTES = TELEGRAM_LIMIT_KILOS * 1024