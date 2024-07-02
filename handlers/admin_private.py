import logging
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_assambly_all

from handlers.admin_routers.logo_handlers import logo_handlers_router
from handlers.admin_routers.assambly_handlers import assambly_handlers_router
from handlers.admin_routers.page_handlers import page_handlers_router

from filters.chat_types import ChatTypeFilter, IsAdmin
from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())
admin_router.include_router(logo_handlers_router)
admin_router.include_router(assambly_handlers_router)
admin_router.include_router(page_handlers_router)



ADMIN_KB = get_keyboard(
    "Добавить инструкцию",
    "Просмотреть инструкции",
    "Добавить страницу",
    "Просмотреть",
    "Изменить лого",
    "Просмотреть лого",
    placeholder="Выберите действие",
    sizes=(2,),
)


@admin_router.message(Command("admin"))
async def add_page_start(message: types.Message, session: AsyncSession):
    assambly = await orm_get_assambly_all(session)
    logging.info('Start admin')
    if assambly:
        await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)
    else:
        await message.answer(
            "Необходимо создать инструкцию",
            reply_markup=get_callback_btns(
                btns={
                    "Создать первую инструкцию": "create_assamble",
                }
            ),
        )
