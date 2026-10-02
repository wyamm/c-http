import time
from pydantic import BaseModel
class Bookie(BaseModel):
    def __init__(self, name: str, balance: float = 0, pnl: float = 0,
                 bonus: float = 0, bonus_reset=None,
                 loss_back: float=0.0, can_use_loss_back: bool=False, loss_back_reset=None, traded: bool=False):
        self.name = name
        self.balance = balance
        self.pnl = pnl
        self.bonus = bonus
        self.bonus_reset = bonus_reset
        self.loss_back = loss_back
        self.can_use_loss_back = can_use_loss_back
        self.loss_back_reset = loss_back_reset
        self.traded = traded
        self.odds = []

    def effective_balance(self) -> float:
        if self.bonus:
            return self.balance + self.bonus
        return self.balance

class EventConfigs(BaseModel):
    team :str
    abrv: str
    market: str
    game_name: str
    outcomes : list[str]