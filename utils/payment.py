import hashlib
import requests
import json
from core import config


def generate_token(params, secret_key):
    # Добавляем пароль в параметры
    params['Password'] = secret_key

    # Сортируем параметры по ключу в алфавитном порядке
    sorted_params = sorted(params.items())

    # Конкатенируем только значения параметров в одну строку
    concatenated_values = ''.join(str(value) for key, value in sorted_params)

    # Применяем SHA-256 хеширование
    token = hashlib.sha256(concatenated_values.encode('utf-8')).hexdigest()

    return token


def initiate_payment(order_id, amount, description, success_url=None, fail_url=None):
    terminal_key = config.payment.TerminalKey
    secret_key = config.payment.SecretKey

    print(terminal_key, secret_key)

    headers = {"Content-Type": "application/json"}

    payment_data = {
        "TerminalKey": terminal_key,
        "Amount": amount,  # Сумма в копейках
        "OrderId": order_id,
        "Description": description
    }

    if success_url:
        payment_data["SuccessURL"] = success_url
    if fail_url:
        payment_data["FailURL"] = fail_url

    token = generate_token(payment_data, secret_key)
    payment_data['Token'] = token

    url = "https://rest-api-test.tinkoff.ru/v2/Init"

    response = requests.post(url, data=json.dumps(payment_data), headers=headers)

    if response.status_code == 200:
        response_data = response.json()

        if response_data.get('Success'):
            print("Платеж инициирован успешно.")
            print(f"Payment ID: {response_data.get('PaymentId')}")
            print(f"Status: {response_data.get('Status')}")
            print(f"Payment URL: {response_data.get('PaymentURL')}")
            return response_data
        else:
            print(f"Ошибка инициализации платежа. Код ошибки: {response_data.get('ErrorCode')}")
            return None
    else:
        print(f"Ошибка при инициации платежа: {response.status_code}, {response.text}\n")
        print(response)
        return None
