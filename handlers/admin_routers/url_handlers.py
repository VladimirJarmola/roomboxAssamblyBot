import logging
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import orm_add_assambly_url, orm_get_assambly, orm_update_assambly_delete_url

from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard


url_handlers_router = Router()

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


class AddURL(StatesGroup):
    URL = State()

    assambly_for_change = None


@url_handlers_router.callback_query(F.data.startswith('url_assambly_'))
async def url_assambly(callback: types.CallbackQuery, session: AsyncSession):
    assambly_id = callback.data.split("_")[-1]
    assambly = await orm_get_assambly(session, assambly_id)
    await callback.answer()
    if assambly.url is None:
        await callback.message.edit_reply_markup(
            reply_markup=get_callback_btns(
                    btns={ 
                        "Добавить URL": f"url_add_assambly_{assambly_id}",
                    }
                )
            )
    else:
        await callback.message.edit_reply_markup(
            reply_markup=get_callback_btns(
                    btns={
                        "Удалить URL": f"url_delete_assambly_{assambly_id}", 
                        "Изменить URL": f"url_add_assambly_{assambly_id}"
                    }
                )
            )
        

@url_handlers_router.callback_query(F.data.startswith('url_add_assambly_'))
async def add_assambly_url(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):

    assambly_id = callback.data.split("_")[-1]
    assambly_for_change = await orm_get_assambly(session, int(assambly_id))
    AddURL.assambly_for_change = assambly_for_change

    await callback.answer()
    await callback.message.answer(
        'Отправь мне УРЛ!', reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddURL.URL)


@url_handlers_router.message(StateFilter(AddURL), Command("отмена"))
@url_handlers_router.message(StateFilter(AddURL), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@url_handlers_router.message(StateFilter(AddURL.URL), F.text)
async def get_assambly_url(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text.find('://') < 0:
        await message.answer('Необходимо отправить url!!!')
        return

    await state.update_data(URL=message.text)
    data = await state.get_data()
    
    id = AddURL.assambly_for_change.id

    try:
        await orm_add_assambly_url(session, id, data)
        await message.answer('URL добавлен', reply_markup=ADMIN_KB)
    except Exception as e:
        logging.exception(e)
        await message.answer(f"Ошибка:  \n{str(e)}\n", reply_markup=ADMIN_KB)
    finally:
        await state.clear()

@url_handlers_router.message(StateFilter(AddURL.URL))
async def get_assambly_url_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте текст!!!")

@url_handlers_router.callback_query(F.data.startswith('url_delete_assambly_'))
async def url_assambly_delete(callback: types.CallbackQuery, session: AsyncSession):
    assambly_id = callback.data.split('_')[-1]
    try: 
        await orm_update_assambly_delete_url(session, assambly_id)
        await callback.message.answer('URL удален!', reply_markup=ADMIN_KB)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer(f"Ошибка:  \n{str(e)}\n", reply_markup=ADMIN_KB)
    finally:
        await callback.answer()
