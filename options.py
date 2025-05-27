import json

options = json.loads(open("options.json").read())
BOT_TOKEN = options.get("token")
if not BOT_TOKEN:
    raise ValueError("Missing token")
PROXY = options.get("proxy")
if not PROXY:
    raise ValueError("Missing proxy")
