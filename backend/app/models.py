from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Bug(Base):
    __tablename__ = "bugs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    component: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="open")
    reported_on: Mapped[date] = mapped_column(Date, default=date.today)
    notes: Mapped[str] = mapped_column(Text, default="")
