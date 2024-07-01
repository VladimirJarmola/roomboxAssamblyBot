import logging
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_add_page, orm_delete_page, orm_get_assambly_all, orm_get_page, orm_get_pages, orm_update_page
from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard


page_handlers_router = Router()


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


class AddPage(StatesGroup):
    assambly = State()
    number = State()
    description = State()
    image = State()

    page_for_change = None

    texts = {
        "AddPage:assambly": "Укажите инструкцию заново",
        "AddPage:number": "Введите номер заново",
        "AddPage:description": "Введите описание заново",
        "AddPage:image": "Это последний стэйт ... ",
    }


@page_handlers_router.message(F.text == "Просмотреть")
async def starring_at_page(message: types.Message, session: AsyncSession):
    assambly = await orm_get_assambly_all(session)
    btns = {
        assambly_item.name: "view_all_" + str(assambly_item.id)
        for assambly_item in assambly
    }
    await message.answer(
        "Выберите инструкцию", reply_markup=get_callback_btns(btns=btns)
    )


@page_handlers_router.callback_query(F.data.startswith("view_all_"))
async def view_pages(callback: types.CallbackQuery, session: AsyncSession):
    assambly_id = callback.data.split("_")[-1]
    pages = await orm_get_pages(session, int(assambly_id))

    if pages:
        for page in pages:
            await callback.answer("Запрос получен")
            await callback.message.answer_photo(
                page.image,
                caption=f"<strong>{page.number}\
                        </strong>\n{page.description}",
                reply_markup=get_callback_btns(
                    btns={
                        "Удалить": f"delete_page_{page.id}",
                        "Изменить": f"change_page_{page.id}",
                    }
                ),
            )
    else:
        await callback.answer("Запрос получен")
        await callback.message.answer(
            "В эту инструкцию не добавлено ни одной страницы", reply_markup=ADMIN_KB
        )


@page_handlers_router.callback_query(F.data.startswith("delete_page_"))
async def delete_page(callback: types.CallbackQuery, session: AsyncSession):
    page_id = callback.data.split("_")[-1]
    await orm_delete_page(session, int(page_id))

    await callback.answer("Лист удален!")
    await callback.message.answer("Лист удален!")


@page_handlers_router.callback_query(StateFilter(None), F.data.startswith("change_page_"))
async def change_page(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    page_id = callback.data.split("_")[-1]

    page_for_change = await orm_get_page(session, int(page_id))

    AddPage.page_for_change = page_for_change

    assambly = await orm_get_assambly_all(session)
    btns = {
        assambly_item.name: "add_page_" + str(assambly_item.id)
        for assambly_item in assambly
    }

    await callback.answer("")
    await callback.message.answer(
        "Выберите инструкцию", reply_markup=get_callback_btns(btns=btns)
    )
    await state.set_state(AddPage.assambly)


# Код ниже для машины состояний Page (FSM)


@page_handlers_router.message(StateFilter(None), F.text == "Добавить страницу")
async def add_page_assambly(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    assambly = await orm_get_assambly_all(session)
    btns = {
        assambly_item.name: "add_page_" + str(assambly_item.id)
        for assambly_item in assambly
    }
    await message.answer(
        "Выберите инструкцию", reply_markup=get_callback_btns(btns=btns)
    )
    await state.set_state(AddPage.assambly)


@page_handlers_router.message(StateFilter(AddPage), Command("отмена"))
@page_handlers_router.message(StateFilter(AddPage), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    if AddPage.page_for_change:
        AddPage.page_for_change = None

    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@page_handlers_router.message(StateFilter(AddPage), Command("назад"))
@page_handlers_router.message(StateFilter(AddPage), F.text.casefold() == "назад")
async def back_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddPage.assambly:
        await message.answer(
            f'Предыдущего шага нет,\nили введите номер страницы,\nили введите "отмена"'
        )
        return

    previous = None
    for step in AddPage.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"ок, вы вернулись к предыдущему шагу \n {AddPage.texts[previous.state]}"
            )
            return
        previous = step


@page_handlers_router.callback_query(
    StateFilter(AddPage.assambly), F.data.startswith("add_page_")
)
async def add_page_number(callback: types.CallbackQuery, state: FSMContext):
    assambly_id = callback.data.split("_")[-1]
    await state.update_data(assambly=assambly_id)
    await callback.answer("Категория выбрана!")
    await callback.message.answer(
        "Укажите номер листа", reply_markup=types.ReplyKeyboardRemove()
    )

    await state.set_state(AddPage.number)


@page_handlers_router.message(StateFilter(AddPage.number), or_f(F.text, F.text == "."))
async def add_description(message: types.Message, state: FSMContext):
    if message.text == "." and AddPage.page_for_change:
        await state.update_data(number=AddPage.page_for_change.number)
    else:
        try:
            int(message.text)
            await state.update_data(number=message.text)
        except Exception as e:
            logging.exception(e)
            await message.answer(f"Ошибка:  \n{str(e)}\nВведите целое число!")
            return

    await message.answer("Введите описание листа инструкции")
    await state.set_state(AddPage.description)


@page_handlers_router.message(StateFilter(AddPage.number))
async def add_description_error(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы ввели недопустимые данные, отправьте текстом целое число!!!"
    )


@page_handlers_router.message(StateFilter(AddPage.description), or_f(F.text, F.text == "."))
async def add_image(message: types.Message, state: FSMContext):
    if message.text == "." and AddPage.page_for_change:
        await state.update_data(description=AddPage.page_for_change.description)
    elif message.text == "..":
        await state.update_data(description="")
    else:
        await state.update_data(description=message.text)

    await message.answer("Загрузите изображение")
    await state.set_state(AddPage.image)


@page_handlers_router.message(StateFilter(AddPage.description))
async def add_image_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте текст!!!")


@page_handlers_router.message(StateFilter(AddPage.image), or_f(F.photo, F.text == "."))
async def add_image3(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == "." and AddPage.page_for_change:
        await state.update_data(image=AddPage.page_for_change.image)
    elif message.text == "." and AddPage.page_for_change is None:
        await message.answer(
            "Здесь необходимо отправить изображение!", reply_markup=ADMIN_KB
        )
        return
    else:
        await state.update_data(image=message.photo[-1].file_id)

    data = await state.get_data()

    try:
        if AddPage.page_for_change:
            await orm_update_page(session, AddPage.page_for_change.id, data)
        else:
            await orm_add_page(session, data)
        await message.answer("Лист инструкции добавлен/изменен", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        logging.exception(e)
        await message.answer(f"Ошибка:  \n{str(e)}\n", reply_markup=ADMIN_KB)
        await state.clear()

    AddPage.page_for_change = None


@page_handlers_router.message(StateFilter(AddPage.image))
async def add_image3_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте изображение!!!")
