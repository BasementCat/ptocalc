from typing import Optional, Self, List
from typing_extensions import Annotated

from pydantic import BaseModel, model_validator, AfterValidator
import arrow

def Ge(n):
    def GeImpl(v):
        if v < n:
            raise ValueError(f"Value must be >= {n}")
        return v
    return GeImpl

def Le(n):
    def LeImpl(v):
        if v > n:
            raise ValueError(f"Value must be <= {n}")
        return v
    return LeImpl


class Holiday(BaseModel):
    name: str
    """Name of this holiday"""

    month: Annotated[int, AfterValidator(Ge(1)), AfterValidator(Le(12))]
    """Month in which this holiday occurs"""

    day: Optional[Annotated[int, AfterValidator(Ge(1)), AfterValidator(Le(31))]] = None
    """Static day of the month on which this holiday occurs"""

    day_of_week: Optional[Annotated[int, AfterValidator(Ge(1)), AfterValidator(Le(7))]] = None
    """Day of the week on which this holiday occurs"""

    occurrence: Optional[Annotated[int, AfterValidator(Ge(-1)), AfterValidator(Le(5))]] = None
    """Week in which this holiday occurs - 1 for first occurrence, 2 for 2nd, etc, or -1 for last"""

    not_weekend: bool = False
    """If True, this holiday is adjusted to fall on the previous non-weekend day"""

    @model_validator(mode='after')
    def validate_config(self) -> Self:
        if self.day and (self.day_of_week or self.occurrence):
            raise ValueError("Must set either day, or day of week and occurrence")

        if not self.day:
            if self.occurrence == 0:
                raise ValueError("occurrence must be -1, or >0")
            if not (self.occurrence and self.day_of_week):
                raise ValueError("Both day_of_week and occurrence must be set")

        return self

    def get_for_year(self, year: int):
        dt = arrow.get(year, self.month, self.day or 1)
        lastmatch = found_dt = None
        if self.day:
            lastmatch = found_dt = dt
        else:
            occurrence = 0
            while True:
                if dt.isoweekday() == self.day_of_week:
                    occurrence += 1
                    lastmatch = arrow.get(dt)
                    if occurrence == self.occurrence:
                        found_dt = lastmatch
                        break
                dt = dt.shift(days=1)
                if dt.month != self.month:
                    break

            if not found_dt and self.occurrence == -1 and lastmatch:
                found_dt = lastmatch

        if found_dt:
            if self.not_weekend:
                while found_dt.isoweekday() in (6, 7):
                    found_dt = found_dt.shift(days=-1)

        return found_dt


class HolidayList(BaseModel):
    holidays: List[Holiday]

    def contains_date(self, dt: arrow.arrow.Arrow) -> Optional[Holiday]:
        for h in self.holidays:
            hdt = h.get_for_year(dt.year)
            if hdt and hdt.year == dt.year and hdt.month == dt.month and hdt.day == dt.day:
                return h

    def find_previous_non_holiday_for_date(self, dt: arrow.arrow.Arrow) -> arrow.arrow.Arrow:
        while self.contains_date(dt):
            dt = dt.shift(days=-1)
        return dt


HOLIDAYS = {
    'US': HolidayList(holidays=[
        Holiday(
            name="New Year's Day",
            month=1,
            day=1,
        ),
        Holiday(
            name="Martin Luther King Jr. Day",
            month=1,
            day_of_week=1,
            occurrence=3,
        ),
        Holiday(
            name="President's Day",
            month=2,
            day_of_week=1,
            occurrence=3,
        ),
        Holiday(
            name="Memorial Day",
            month=5,
            day_of_week=1,
            occurrence=-1,
        ),
        Holiday(
            name="Juneteenth",
            month=6,
            day=19,
        ),
        Holiday(
            name="Independence Day",
            month=7,
            day=4,
            not_weekend=True,
        ),
        Holiday(
            name="Labor Day",
            month=9,
            day_of_week=1,
            occurrence=1,
        ),
        Holiday(
            name="Indigenous People's Day",
            month=10,
            day=12,
        ),
        Holiday(
            name="Veteran's Day",
            month=11,
            day=11,
        ),
        Holiday(
            name="Thanksgiving",
            month=11,
            day_of_week=4,
            occurrence=4,
        ),
        Holiday(
            name="Christmas Eve",
            month=12,
            day=24,
        ),
        Holiday(
            name="Christmas",
            month=12,
            day=25,
        ),
    ]),
}
