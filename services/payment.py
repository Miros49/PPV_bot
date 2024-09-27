import logging
import hmac
import hashlib
import base64
import uvicorn

from typing import Type
from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
from ipaddress import ip_address, ip_network

from core import config
from models import CheckRequest, PayRequest, FailRequest, ConfirmRequest, RefundRequest, CancelRequest


app = FastAPI()


# Проверка, входит ли IP-адрес запроса в список разрешенных
def is_ip_allowed(ip: str) -> bool:
    request_ip = ip_address(ip)
    for network in config.payment.allowed_ips:
        if request_ip in ip_network(network):
            return True
    return False


# Проверка подлинности HMAC
def verify_hmac(request_body: str, received_hmac: str, api_secret: str) -> bool:
    calculated_hmac = hmac.new(
        api_secret.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha256
    ).digest()

    calculated_hmac_base64 = base64.b64encode(calculated_hmac).decode()
    return hmac.compare_digest(calculated_hmac_base64, received_hmac)


# Общий обработчик запросов
async def process_request(request: Request, expected_model: Type[BaseModel], api_secret: str, allowed_ips: list):
    client_ip = request.client.host

    # Проверка IP-адреса
    if not is_ip_allowed(client_ip):
        logging.warning(f"Запрос от неразрешенного IP-адреса: {client_ip}")
        raise HTTPException(status_code=403, detail="Access from this IP is not allowed")

    request_body = await request.body()
    received_hmac = request.headers.get("X-Content-HMAC", "")

    # Проверка HMAC
    if not verify_hmac(request_body.decode('utf-8'), received_hmac, api_secret):
        logging.error("Ошибка проверки HMAC")
        raise HTTPException(status_code=400, detail="Invalid HMAC verification")

    try:
        # Проверка и обработка запроса на основе ожидаемой модели
        request_data = expected_model.parse_raw(request_body)
        logging.info(f"Успешно получен запрос: {request_data}")
        return {"code": 0}
    except Exception as e:
        logging.error(f"Ошибка обработки запроса: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/check")
async def handle_check(request: Request):
    return await process_request(request, CheckRequest, config.payment.api_secret, config.payment.allowed_ips)


@app.post("/pay")
async def handle_pay(request: Request):
    return await process_request(request, PayRequest, config.payment.api_secret, config.payment.allowed_ips)


@app.post("/fail")
async def handle_fail(request: Request):
    return await process_request(request, FailRequest, config.payment.api_secret, config.payment.allowed_ips)


@app.post("/confirm")
async def handle_confirm(request: Request):
    return await process_request(request, ConfirmRequest, config.payment.api_secret, config.payment.allowed_ips)


@app.post("/refund")
async def handle_refund(request: Request):
    return await process_request(request, RefundRequest, config.payment.api_secret, config.payment.allowed_ips)


@app.post("/cancel")
async def handle_cancel(request: Request):
    return await process_request(request, CancelRequest, config.payment.api_secret, config.payment.allowed_ips)


def run_server():
    uvicorn.run("services.payment:app", host=config.server.ip, port=config.server.port, reload=True)
