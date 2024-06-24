from sqlalchemy import DateTime, String, Text, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    update: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Logo(Base):
    __tablename__='logo'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    image: Mapped[str] = mapped_column(String(150))


class Assambly(Base):
    __tablename__='assambly'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(String(150))


class Page(Base):
    __tablename__='page'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(nullable=False, unique=False)
    description: Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(String(150))
    assambly_id: Mapped[int] = mapped_column(ForeignKey('assambly.id', ondelete='CASCADE'), nullable=False)

    assambly: Mapped['Assambly'] = relationship(backref='page')
