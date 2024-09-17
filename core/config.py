from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, Redis

from dataclasses import dataclass
from environs import Env


redis = Redis(host='localhost')
storage = RedisStorage(redis=redis)


@dataclass
class TgBot:
    token: str  # Токен для доступа к боту
    admin_ids: list[int]  # Список id админов


@dataclass
class Payment:
    public_id: str
    api_secret: str


@dataclass
class Config:
    tg_bot: TgBot
    payment: Payment


def load_config(path: str | None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN'),
            admin_ids=list(map(int, env.list('ADMIN_IDS')))
        ),
        payment=Payment(
            public_id=env('PUBLIC_ID'),
            api_secret=env('API_SECRET')
        )
    )


config: Config = load_config('.env')

default = DefaultBotProperties(parse_mode='HTML')
bot: Bot = Bot(token=config.tg_bot.token, default=default)
