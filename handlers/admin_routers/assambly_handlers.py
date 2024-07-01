import logging
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import orm_add_assambly, orm_delete_assambly, orm_get_assambly, orm_get_assambly_all, orm_update_assambly
from kbds.inline import get_callback_btns

from kbds.reply import get_keyboard


assambly_handlers_router = Router()


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

class AddAssambly(StatesGroup):
    name = State()
    description = State()
    image = State()

    assambly_for_change = None

    texts = {
        "AddAssambly:name": "Введите имя заново",
        "AddAssambly:description": "Введите описание заново",
        "AddAssambly:image": "Это последний стэйт ... ",
    }


@assambly_handlers_router.callback_query(StateFilter(None), F.data == "create_assamble")
async def create_assamble(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    await callback.answer("Инструкция создана!")
    await callback.message.answer(
        "Введите название инструкции", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddAssambly.name)


@assambly_handlers_router.message(F.text == "Просмотреть инструкции")
async def starring_at_assambly(message: types.Message, session: AsyncSession):
    for assambly_item in await orm_get_assambly_all(session):
        await message.answer_photo(
            assambly_item.image,
            caption=f"<strong>{assambly_item.name}\
                    </strong>\n{assambly_item.description}",
            reply_markup=get_callback_btns(
                btns={"Удалить": f"delete_assambly_{assambly_item.id}", "Изменить": f"change_assambly_{assambly_item.id}"}
            ),
        )


@assambly_handlers_router.callback_query(F.data.startswith("delete_assambly_"))
async def delete_assambly(callback: types.CallbackQuery, session: AsyncSession):
    assambly_id = callback.data.split("_")[-1]
    await orm_delete_assambly(session, int(assambly_id))

    await callback.answer("Инструкция удалена!")
    await callback.message.answer("Инструкция удалена!")


@assambly_handlers_router.callback_query(StateFilter(None), F.data.startswith("change_assambly_"))
async def change_assambly(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    assambly_id = callback.data.split("_")[-1]

    assambly_for_change = await orm_get_assambly(session, int(assambly_id))

    AddAssambly.assambly_for_change = assambly_for_change

    await callback.answer("Инструкция изменена!")
    await callback.message.answer(
        "Введите название инструкции", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddAssambly.name)


# Код ниже для машины состояний Assambly (FSM)


@assambly_handlers_router.message(StateFilter(None), F.text == "Добавить инструкцию")
async def add_assambly(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название инструкции", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddAssambly.name)


@assambly_handlers_router.message(StateFilter(AddAssambly), Command("отмена"))
@assambly_handlers_router.message(StateFilter(AddAssambly), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    if AddAssambly.assambly_for_change:
        AddAssambly.assambly_for_change = None

    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@assambly_handlers_router.message(StateFilter(AddAssambly), Command("назад"))
@assambly_handlers_router.message(StateFilter(AddAssambly), F.text.casefold() == "назад")
async def back_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddAssambly.name:
        await message.answer(
            f'Предыдущего шага нет,\nили введите название,\nили введите "отмена"'
        )
        return

    previous = None
    for step in AddAssambly.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"ок, вы вернулись к предыдущему шагу \n {AddAssambly.texts[previous.state]}"
            )
            return
        previous = step


@assambly_handlers_router.message(StateFilter(AddAssambly.name), or_f(F.text, F.text == "."))
async def add_assambly_name(message: types.Message, state: FSMContext):
    if message.text == "." and AddAssambly.assambly_for_change:
        await state.update_data(name=AddAssambly.assambly_for_change.name)
    else:
        await state.update_data(name=message.text)

    await message.answer("Введите описание инструкции")
    await state.set_state(AddAssambly.description)


@assambly_handlers_router.message(StateFilter(AddAssambly.name))
async def add_assambly_name_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте текст!!!")


@assambly_handlers_router.message(StateFilter(AddAssambly.description), or_f(F.text, F.text == "."))
async def add_assambly_description(message: types.Message, state: FSMContext):
    if message.text == "." and AddAssambly.assambly_for_change:
        await state.update_data(description=AddAssambly.assambly_for_change.description)
    elif message.text == "..":
        await state.update_data(description="")
    else:
        await state.update_data(description=message.text)

    await message.answer("Загрузите изображение")
    await state.set_state(AddAssambly.image)


@assambly_handlers_router.message(StateFilter(AddAssambly.description))
async def add_assambly_description_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте текст!!!")


@assambly_handlers_router.message(StateFilter(AddAssambly.image), or_f(F.photo, F.text == "."))
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    
    if message.text and message.text == "." and AddAssambly.assambly_for_change:
        await state.update_data(image=AddAssambly.assambly_for_change.image)
    elif message.text == "." and AddAssambly.assambly_for_change is None:
        await message.answer('Необходимо отправить изображение!', reply_markup=ADMIN_KB)
        return
    else:
        await state.update_data(image=message.photo[-1].file_id)

    data = await state.get_data()

    try:
        if AddAssambly.assambly_for_change:
            await orm_update_assambly(session, AddAssambly.assambly_for_change.id, data)
        else:
            await orm_add_assambly(session, data)
        await message.answer("Лист инструкции добавлен/изменен", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        logging.exception(e)
        await message.answer(f"Ошибка:  \n{str(e)}\n", reply_markup=ADMIN_KB)
        await state.clear()

    AddAssambly.page_for_change = None


@assambly_handlers_router.message(StateFilter(AddAssambly.image))
async def add_image2_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте изображение!!!")
