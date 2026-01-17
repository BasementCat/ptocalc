from typing import Optional, List, Self, Dict, Any, Union, Tuple, Literal

from pydantic import BaseModel as PydanticBaseModel, field_validator, model_validator, field_serializer, Field
import arrow

from .dates import Holiday, HolidayList, HOLIDAYS



class BaseModel(PydanticBaseModel):
    pass
    # parent: Any = Field(default=None, exclude=True)

    # @classmethod
    # def _add_parent_to(cls, parent, obj):
    #     if isinstance(obj, BaseModel):
    #         print("add parent", parent, "to", obj)
    #         obj.parent = parent
    #     elif isinstance(obj, list):
    #         print("found list, iterating")
    #         for sub in obj:
    #             cls._add_parent_to(parent, sub)
    #     elif isinstance(obj, dict):
    #         print("found dict, iterating")
    #         for sub in obj.values():
    #             cls._add_parent_to(parent, sub)

    # @model_validator(mode='after')
    # def add_parent(self) -> Self:
    #     print("add parent, called on", self)
    #     for field in self.__fields__.keys():
    #         print("add to prop:", field)
    #         self._add_parent_to(self, getattr(self, field, None))
    #     return self


class PTOAdjustment(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    date: arrow.arrow.Arrow
    pto_type: Optional['PTOType'] = None
    hours: float
    # hours_running__confirmed: float = 0.0
    # hours_running__type: float = 0.0
    pto: Optional['PTOEntry'] = None


class PTOType(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    accruals: List[PTOAdjustment] = Field(default=[], exclude=True)

    name: str
    """Name of this PTO type"""

    short: Optional[str] = None
    """Optional short name of this PTO type"""

    order: int = 0
    """Sort order to use during calculations"""

    rollover: float = 0
    """Number of hours rolled over from the previous year"""

    accrued: bool = True
    """If true, PTO is accrued over time, otherwise the balance is immediately available and total must be set"""

    accrual_weeks: Optional[int] = None
    """If set, pay periods occur this many weeks apart (ex. every 2 weeks)"""

    accrual_days: Optional[List[int]] = None
    """If set, pay periods occur on these days of the month (ex. 15, -1 for the 15th and last day)"""

    accrual_amount: Optional[float] = None
    """Amount of PTO accrued per pay period in hours, may be calculated from total"""

    total: Optional[float] = None
    """Total amount of PTO accrued for the year, if accrued is False this must be set, otherwise it is used to calculate accrual_amount (divided by # of pay periods)"""

    @model_validator(mode='after')
    def check_data(self, info) -> Self:
        if self.rollover:
            self.accruals += [PTOAdjustment.model_validate({
                'date': arrow.get(info.context['year'], 1, 1, tzinfo=info.context['timezone']),
                # 'pto_type': self,
                'hours': self.rollover,
            }, context=info.context)]
        if self.accrued:
            if bool(self.accrual_weeks) == bool(self.accrual_days):
                raise ValueError("If accrued, one of accrual_days or accrual_weeks is required")
            if bool(self.accrual_amount) == bool(self.total):
                raise ValueError("Only one of accrual_amount or total is required/allowed")

            if self.accrual_weeks:
                pay_periods = int(52 / self.accrual_weeks)
            else:
                pay_periods = 12 * len(self.accrual_days)

            if not self.accrual_amount:
                self.accrual_amount = self.total / float(pay_periods)
            elif not self.total:
                self.total = self.accrual_amount * pay_periods

            # Calculate all accrual dates
            dates = []
            if self.accrual_weeks:
                # TODO: this should have an actual start date; may not be 1/1
                date = arrow.get(info.context['year'], 1, 1, tzinfo=info.context['timezone']).shift(weeks=self.accrual_weeks)
                while date.year == info.context['year']:
                    dates.append(date)
                    date = date.shift(weeks=self.accrual_weeks)
            else:
                for month in range(1, 13):
                    for day in self.accrual_days:
                        if day == -1:
                            date = arrow.get(info.context['year'], month, 1, tzinfo=info.context['timezone']) \
                                .shift(months=1) \
                                .shift(days=-1)
                        else:
                            date = arrow.get(info.context['year'], month, day, tzinfo=info.context['timezone'])
                        while date.isoweekday() in (6, 7):
                            date = date.shift(days=-1)
                        date = info.context['bank_holidays'].find_previous_non_holiday_for_date(date)
                        dates.append(date)
            self.accruals += [PTOAdjustment.model_validate({
                'date': d,
                # 'pto_type': self,
                'hours': self.accrual_amount
            }, context=info.context) for d in dates]
        else:
            if not self.total:
                raise ValueError("total is required")

            self.accruals += [PTOAdjustment.model_validate({
                'date': arrow.get(info.context['year'], 1, 1, tzinfo=info.context['timezone']),
                # 'pto_type': self,
                'hours': self.total,
            }, context=info.context)]
        for a in self.accruals:
            a.pto_type = self

        return self

    @property
    def short_name(self):
        return self.short or self.name


class PTOEntry(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    name: str
    """Name/description of this PTO entry"""

    pto_type: str
    """Key of the PTO type to use"""

    start: Union[str, arrow.arrow.Arrow]
    """Start date of this PTO"""

    hours: Optional[float] = None
    """Duration, in hours, of this PTO entry"""

    days: Optional[float] = None
    """Duration, in days, of this PTO entry"""

    end: Optional[Union[str, arrow.arrow.Arrow]] = None
    """End date of this PTO entry"""

    start_half: bool = False
    """If true, the starting day of the PTO is a half day"""

    end_half: bool = False
    """If true, the ending day of the PTO is a half day"""

    tentative: bool = False
    """If true, this entry is tentative and not included by default"""

    requested: bool = False
    """If true, this entry has been requested off"""

    approved: Optional[bool] = None
    """If none, this entry is considered to be pending, otherwise it is approved or rejected"""

    travel: Optional[bool] = None
    """If none, this entry does not require arranging travel, otherwise indicates whether travel has been arranged"""

    lodging: Optional[bool] = None
    """If none, this entry does not require arranging lodging, otherwise indicates whether lodging has been arranged"""

    registration: Optional[bool] = None
    """If none, this entry does not require arranging registration, otherwise indicates whether registration has been arranged"""

    roommates: Optional[bool] = None
    """If none, this entry does not require arranging roommates, otherwise indicates whether roommates has been arranged"""

    @model_validator(mode='after')
    def parse_and_check(self, info) -> Self:
        if self.pto_type not in info.context['pto_types']:
            raise ValueError("Invalid PTO type")

        self.start = arrow.get(self.start, tzinfo=info.context['timezone']).replace(hour=info.context['working_hours'][0], minute=0, second=0, microsecond=0)
        if self.end:
            self.end = arrow.get(self.end, tzinfo=info.context['timezone']).replace(hour=info.context['working_hours'][1], minute=0, second=0, microsecond=0)
        else:
            self.end = self.start.replace(hour=info.context['working_hours'][1])

        full_len = int(info.context['working_hours'][1] - info.context['working_hours'][0])
        half_len = int(full_len / 2)
        if self.start_half:
            self.start = self.start.shift(hours=half_len)
        if self.end_half:
            self.end = self.end.shift(hours=-half_len)

        if self.start == self.end:
            raise ValueError("Start and end times are the same")

        if not (self.days or self.hours):
            # need to calculate
            hours = 0
            date = self.start.replace(hour=0)
            end = self.end.replace(hour=0).shift(days=1)
            while date < end:
                # Weekend or holiday
                if not (date.isoweekday() in (6, 7) or info.context['holidays'].contains_date(date)):
                    if (
                        (date == self.start.replace(hour=0) and self.start_half)
                        or (date == self.end.replace(hour=0) and self.end_half)
                    ):
                        # date is start & start is half, or same for end
                        hours += half_len
                    else:
                        hours += full_len
                date = date.shift(days=1)
            self.hours = hours

        if self.days and not self.hours:
            self.hours = self.days * 8.0
        if self.hours and not self.days:
            self.days = self.hours / 8.0

        if self.hours != self.days * 8.0:
            raise ValueError("Mismatch between hours and days")

        return self

    @field_serializer('start')
    def serialize_start(self, value):
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


class PTOYear(BaseModel):
    name: str
    year: int
    timezone: str
    working_hours: Tuple[int, int]
    bank_holidays: Union[HolidayList, List[Union[Literal['default', 'US'], str, Holiday]]]
    holidays: Union[HolidayList, List[Union[Holiday, str]]] = []
    pto_types: Dict[str, PTOType] = {}
    pto_entries: List[PTOEntry] = []

    @field_validator('bank_holidays', mode='after')
    @classmethod
    def parse_bank_holidays(cls, v, info):
        if not isinstance(v, HolidayList):
            items = []
            for item in v:
                if isinstance(item, str):
                    if item == 'default':
                        items += HOLIDAYS['US'].holidays
                    elif item in ('US',):
                        items += HOLIDAYS[item].holidays
                    else:
                        assert item.startswith('-')
                        item = item[1:]
                        items = [i for i in items if i.name != item]
                else:
                    items.append(item)
            v = HolidayList(holidays=items)
        info.context['bank_holidays'] = v
        return v

    @field_validator('holidays', mode='after')
    @classmethod
    def parse_holidays(cls, v, info):
        if not isinstance(v, HolidayList):
            bh_by_name = {h.name: h for h in info.context['bank_holidays'].holidays} if info.context.get('bank_holidays') else {}
            items = []
            for item in v:
                if isinstance(item, str):
                    item = bh_by_name.get(item)
                if item:
                    items.append(item)
            v = HolidayList(holidays=items)
        info.context['holidays'] = v
        return v

    @field_validator('*', mode='after')
    @classmethod
    def add_context(cls, v, info):
        if info.field_name in ('year', 'timezone', 'working_hours', 'pto_types'):
            info.context[info.field_name] = v
        return v

    @property
    def adjustments(self):
        out = []
        for t in self.pto_types.values():
            out += t.accruals
        for e in self.pto_entries:
            a = PTOAdjustment.model_validate({
                'date': e.start,
                'hours': -e.hours,
            }, context={'year': self.year, 'timezone': self.timezone})
            a.pto_type = self.pto_types[e.pto_type]
            a.pto = e
            out.append(a)
        return out


class PTOFile(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    collections: List[PTOYear] = []
