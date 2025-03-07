from decimal import Decimal


class PurchaseListObject:
    stock_code: str
    purchase_amount: Decimal
    purchase_price: float


class AccountStatus:
    initial_nav: Decimal
    current_nav: Decimal


class TickerInfo:
    weight: float = 0
    target_nav: Decimal = 0
    fee: Decimal = 0
    before_nav: Decimal = 0
    after_nav: Decimal = 0
    momentum: float = 0
    profit_rate: float = 0
    current_price: float = 0
