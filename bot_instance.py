from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from config import API_TOKEN

bot = Bot(token=API_TOKEN, session=AiohttpSession())
