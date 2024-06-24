import math
from tkinter import NO
from unittest import result
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Assambly, Logo, Page


##### Paginator #####

class Paginator:
    def __init__(self, array: list | tuple, page: int=1, per_page: int=1):
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)
        # math.ceil - округление в большую сторону до целого числа
        self.pages = math.ceil(self.len / self.per_page)

    def __get_slice(self):
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def get_page(self):
        page_items = self.__get_slice()
        return page_items

    def has_next(self):
        if self.page < self.pages:
            return self.page + 1
        return False

    def has_previous(self):
        if self.page > 1:
            return self.page - 1
        return False

    def get_next(self):
        if self.page < self.pages:
            self.page += 1
            return self.get_page()
        raise IndexError(f'Next page does not exist. Use has_next() to check before.')

    def get_previous(self):
        if self.page > 1:
            self.page -= 1
            return self.__get_slice()
        raise IndexError(f'Previous page does not exist. Use has_previous() to check before.')


##### First Screen
    
async def orm_add_first_screen(session: AsyncSession, data: dict):
    session.add(Logo(image=data['image']))
    await session.commit()

async def orm_get_logo(session: AsyncSession):
    query = select(Logo)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_update_logo(session: AsyncSession, data: dict, logo_id: int):
    query_update = update(Logo).where(Logo.id == logo_id).values(image=data['image'])
    await session.execute(query_update)
    await session.commit()

#### Assambly
async def orm_add_assambly(session: AsyncSession, data: dict):
    obj = Assambly(
        name=data['name'],
        description=data['description'],
        image=data['image']
    )
    session.add(obj)
    await session.commit()


async def orm_get_assambly_all(session: AsyncSession):
    query = select(Assambly)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_assambly(session: AsyncSession, assambly_id: int):
    query = select(Assambly).where(Assambly.id == assambly_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_assambly(session: AsyncSession, assambly_id: int, data):
    query = update(Assambly).where(Assambly.id == assambly_id).values(
        name=data['name'],
        description=data['description'],
        image=data['image'],
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_assambly(session: AsyncSession, assambly_id: int):
    query = delete(Assambly).where(Assambly.id == assambly_id)
    await session.execute(query)
    await session.commit()


##### Page
#Записывает в бд страницу
async def orm_add_page(session: AsyncSession, data: dict):
    obj = Page(
        assambly_id=int(data['assambly']),
        number=int(data['number']),
        description=data['description'],
        image=data['image'],
    )
    session.add(obj)
    await session.commit()


#Получаем из бд все страницы инструкции
async def orm_get_pages(session: AsyncSession, assambly_id):
    query = select(Page).where(Page.assambly_id == int(assambly_id)).order_by(Page.number)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_page(session: AsyncSession, page_id: int):
    query = select(Page).where(Page.id == page_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_page(session: AsyncSession, page_id: int, data):
    query = update(Page).where(Page.id == page_id).values(
        number=int(data['number']),
        description=data['description'],
        image=data['image'],
        assambly_id=int(data['assambly'])
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_page(session: AsyncSession, page_id: int):
    query = delete(Page).where(Page.id == page_id)
    await session.execute(query)
    await session.commit()
