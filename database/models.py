from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    update: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Page(Base):
    __tablename__='page'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(String(150))
