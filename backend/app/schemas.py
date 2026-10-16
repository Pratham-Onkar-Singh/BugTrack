from datetime import date
from typing import Annotated, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Status = Literal["open", "investigating", "resolved", "closed"]
STATUSES = get_args(Status)
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class BugIn(BaseModel):
    title: Text
    component: Text
    status: Status = "open"
    reported_on: date = Field(default_factory=date.today)
    notes: str = ""


class BugOut(BugIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class Stats(BaseModel):
    total: int
    open: int
    investigating: int
    resolved: int
    closed: int
