from typing import Optional, List, Self, Dict

from pydantic import BaseModel, model_validator, field_serializer
import arrow


class PTOType(BaseModel):
    key: str
    name: str
    short: Optional[str] = None
    order: int = 0
    init_balance: float = 0
    balance: float = 0
    resolution: float = 1
    accrued: bool = True
    accrual_days: Optional[List[int]] = None
    accrual_amount: Optional[float] = None
    accrual_total: Optional[float] = None

    @model_validator(mode='after')
    def check_data(self) -> Self:
        if self.accrued:
            if not self.accrual_days:
                raise ValueError("If accrued, accrual_days is required")
            if bool(self.accrual_amount) == bool(self.accrual_total):
                raise ValueError("Only one of accrual_amount/accrual_total is required/allowed")
        return self

    @property
    def short_name(self):
        return self.short or self.name


class PTOEntry(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    name: str
    pto_type: str
    date: arrow.arrow.Arrow
    amount: float
    end: Optional[arrow.arrow.Arrow] = None
    tentative: bool = False
    requested: bool = False
    approved: bool = False
    travel: Optional[bool] = None
    lodging: Optional[bool] = None
    registration: Optional[bool] = None
    roommates: Optional[bool] = None

    @model_validator(mode='before')
    def parse_before(cls, data):
        if isinstance(data, dict):
            if data.get('date'):
                data['date'] = arrow.get(data['date'])
            if data.get('end'):
                data['end'] = arrow.get(data['end'])
        return data

    @field_serializer('date')
    def serialize_date(self, value):
        return str(value)

    @field_serializer('end')
    def serialize_end(self, value):
        if value:
            return str(value)
        return value

    # def apply_to_balance(self, balances: Dict[str, PTOType]):
    #     bal = balances[self.pto_type]
    #     if self._add:
    #         bal.balance += self.amount
    #     else:
    #         bal.balance -= self.amount


class PTOCollection(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    filename: Optional[str] = None
    start: arrow.arrow.Arrow
    pto_types: List[PTOType] = []
    entries: List[PTOEntry] = []

    @model_validator(mode='before')
    def parse_before(cls, data):
        if isinstance(data, dict):
            if data.get('start'):
                data['start'] = arrow.get(data['start'])
        return data

    @field_serializer('start')
    def serialize_start(self, value):
        return str(value)
