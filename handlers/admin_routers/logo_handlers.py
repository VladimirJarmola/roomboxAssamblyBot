import logging
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_add_first_screen, orm_get_logo, orm_update_logo

from kbds.reply import get_keyboard


logo_handlers_router = Router()

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

class AddLogo(StatesGroup):
    image = State()


####### LOGO ######
@logo_handlers_router.message(F.text == "Просмотреть лого")
async def starring_at_logo(message: types.Message, session: AsyncSession):
    logo = await orm_get_logo(session)
    if logo:
        for logo_item in logo:
            await message.answer_photo(logo_item.image)
    else: 
        await message.answer(
            "Сначала добавь изображение логотипа", reply_markup=ADMIN_KB
        )

# Код ниже для машины состояний Logo (FSM)

@logo_handlers_router.message(StateFilter(None), F.text == "Изменить лого")
async def add_logo(message: types.Message, state: FSMContext):
    await message.answer(
        "Отправьте изображение логотипа", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddLogo.image)


@logo_handlers_router.message(StateFilter(AddLogo), Command("отмена"))
@logo_handlers_router.message(StateFilter(AddLogo), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@logo_handlers_router.message(StateFilter(AddLogo.image), F.photo)
async def add_image_logo(message: types.Message, state: FSMContext, session: AsyncSession):

    await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()

    current_logo = await orm_get_logo(session)

    count = 0
    for item in current_logo:
        count += 1
        if count == 1:
            logo_id = item.id
        else:
            break

    if current_logo:
        try:
            await orm_update_logo(session, data, logo_id)
            await state.clear()
            await message.answer("Лого изменен", reply_markup=ADMIN_KB)

        except Exception as e:
            logging.exception(e)
            await message.answer(f"Ошибка:  \n{str(e)}\n", reply_markup=ADMIN_KB)
            await state.clear()
    else:
        try: 
            await orm_add_first_screen(session, data)
            await state.clear()
            await message.answer("Лого добавлен", reply_markup=ADMIN_KB)

        except Exception as e:
            logging.exception(e)
            await message.answer(f"Ошибка:  \n{str(e)}\n", reply_markup=ADMIN_KB)
            await state.clear()

@logo_handlers_router.message(StateFilter(AddLogo.image))
async def add_image_logo_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте изображение!!!")
