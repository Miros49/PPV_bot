from aiogram.fsm.storage.memory import MemoryStorage

from dataclasses import dataclass
from environs import Env


user_data = {}
active_chats = {}
cancel_requests = {}

storage = MemoryStorage()


@dataclass
class TgBot:
    token: str  # Токен для доступа к боту
    admin_ids: list[int]  # Список id админов


@dataclass
class Payment:
    token: str


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
        payment=Payment(token=env('PAYMENT_TOKEN'))
    )
