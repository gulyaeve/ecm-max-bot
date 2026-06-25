from maxapi import Bot, Dispatcher

from config import settings


bot = Bot(settings.MAX_BOT_TOKEN)
dp = Dispatcher()