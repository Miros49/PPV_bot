import json
import logging
from fastapi import Request, HTTPException
from aiogram import Bot

logging.basicConfig(level=logging.INFO)


class CloudPaymentsHandler:
    def __init__(self, bot: Bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id

    async def handle_payment_notification(self, request: Request):
        print(12345675432345)
        try:
            data = await request.json()
            logging.info(f"Получены данные от CloudPayments: {data}")

            if 'TransactionId' not in data or 'Amount' not in data or 'Status' not in data:
                logging.error("Некорректные данные: отсутствуют необходимые поля")
                raise HTTPException(status_code=400, detail="Missing required fields")

            transaction_id = data['TransactionId']
            amount = data['Amount']
            status = data['Status']

            if status == 'Completed':
                await self.bot.send_message(chat_id=self.chat_id,
                                            text=f"Оплата успешна! Транзакция: {transaction_id}, Сумма: {amount}")
                logging.info(f"Успешная оплата: транзакция {transaction_id}, сумма {amount}")
                return {"code": 0}
            else:
                await self.bot.send_message(chat_id=self.chat_id,
                                            text=f"Платеж не прошел. Статус: {status}")
                logging.warning(f"Платеж не прошел: транзакция {transaction_id}, статус {status}")
                return {"code": 1, "message": "Payment failed"}

        except json.JSONDecodeError:
            logging.error("Ошибка при декодировании JSON")
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        except Exception as e:
            logging.error(f"Ошибка при обработке уведомления: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
