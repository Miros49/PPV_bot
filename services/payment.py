import json
import logging
from fastapi import FastAPI, Request
from aiogram import Bot

logging.basicConfig(level=logging.INFO)


class CloudPaymentsHandler:
    def __init__(self, bot: Bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id

    async def handle_payment_notification(self, request: Request):
        try:
            data = await request.json()

            transaction_id = data.get('TransactionId')
            amount = data.get('Amount')
            status = data.get('Status')

            if status == 'Completed':
                await self.bot.send_message(chat_id=self.chat_id,
                                            text=f"Оплата успешна! Транзакция: {transaction_id}, Сумма: {amount}")
                return {"code": 0}
            else:
                await self.bot.send_message(chat_id=self.chat_id,
                                            text=f"Платеж не прошел. Статус: {status}")
                return {"code": 1, "message": "Payment failed"}

        except Exception as e:
            logging.error(f"Ошибка при обработке уведомления: {str(e)}")
            return {"code": 1, "message": "Internal server error"}
