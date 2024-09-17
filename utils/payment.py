import asyncio
import aiohttp
import base64

from core import config

API_URL = "https://api.cloudpayments.ru/orders/create"


def get_auth_header() -> str:
    auth_string = f"{config.payment.public_id}:{config.payment.api_secret}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    return f"Basic {auth_base64}"


async def create_invoice(amount: float, email: str, invoice_id: str,
                         account_id: str, description: str = 'Пополнение счёта',
                         currency: str = "RUB", send_email: bool = False,
                         offer_uri: str = None, phone: str = None,
                         send_sms: bool = False, culture_name: str = "ru-RU",
                         success_redirect_url: str = None,
                         fail_redirect_url: str = None) -> dict:
    headers = {
        "Authorization": get_auth_header(),
        "Content-Type": "application/json"
    }

    payload = {
        "Amount": amount,
        "Currency": currency,
        "Description": description,
        "Email": email,
        "RequireConfirmation": False,
        "SendEmail": send_email,
        "InvoiceId": invoice_id,
        "AccountId": account_id

    }

    if offer_uri:
        payload["OfferUri"] = offer_uri
    if phone:
        payload["Phone"] = phone
    if send_sms:
        payload["SendSms"] = send_sms
    if culture_name:
        payload["CultureName"] = culture_name
    if success_redirect_url:
        payload["SuccessRedirectUrl"] = success_redirect_url
    if fail_redirect_url:
        payload["FailRedirectUrl"] = fail_redirect_url

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload, headers=headers) as response:
            if response.status == 200:
                response_data = await response.json()
                if response_data.get("Success"):
                    return response_data
                else:
                    raise Exception(f"Error creating invoice: {response_data.get('Message')}")
            else:
                text = await response.text()
                raise Exception(f"Failed to create invoice. Status: {response.status}, Response: {text}")


async def test():
    try:
        response = await create_invoice(
            amount=10.0,
            description="Оплата на сайте example.com",
            email="client@test.local",
            send_email=True,
            invoice_id='3',
            account_id='0'
        )
        print(response)
    except Exception as e:
        print(f"Failed to create invoice: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test())
