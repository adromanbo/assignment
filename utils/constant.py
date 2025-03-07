

class PurchaseListObject:
    stock_code: str
    purchase_amount: float
    purchase_price: float


class AccountStatus:
    initial_nav: float
    current_nav: float


class TickerInfo:
    weight: float = 0
    target_nav: float = 0
    fee: float = 0
    before_nav: float = 0
    after_nav: float = 0
    momentum: float = 0
    profit_rate: float = 0
    current_price: float = 0
