from pydantic import BaseModel


class CheckRequest(BaseModel):
    TransactionId: int
    Amount: float
    Currency: str
    PaymentAmount: str
    PaymentCurrency: str
    DateTime: str
    CardFirstSix: str
    CardLastFour: str
    CardType: str
    CardExpDate: str
    TestMode: int
    Status: str
    OperationType: str
    CardId: str = None
    InvoiceId: str = None
    AccountId: str = None
    SubscriptionId: str = None
    TokenRecipient: str = None
    Name: str = None
    Email: str = None
    IpAddress: str = None
    IpCountry: str = None
    IpCity: str = None
    IpRegion: str = None
    IpDistrict: str = None
    IpLatitude: str = None
    IpLongitude: str = None
    Issuer: str = None
    IssuerBankCountry: str = None
    Description: str = None
    CardProduct: str = None
    PaymentMethod: str = None
    Data: dict = None


# Другие модели аналогичны CheckRequest и содержат соответствующие обязательные и необязательные поля.
class PayRequest(CheckRequest):
    GatewayName: str


class FailRequest(CheckRequest):
    Reason: str
    ReasonCode: int


class ConfirmRequest(CheckRequest):
    AuthCode: str = None


class RefundRequest(BaseModel):
    TransactionId: int
    PaymentTransactionId: int
    Amount: float
    DateTime: str
    OperationType: str
    InvoiceId: str = None
    AccountId: str = None
    Email: str = None
    Data: dict = None
    Rrn: str = None


class CancelRequest(BaseModel):
    TransactionId: int
    Amount: float
    DateTime: str
    InvoiceId: str = None
    AccountId: str = None
    Email: str = None
    Data: dict = None
    Rrn: str = None
