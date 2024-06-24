import logging
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_add_assambly,
    orm_add_first_screen,
    orm_get_logo,
    orm_add_page,
    orm_delete_assambly,
    orm_delete_page,
    orm_get_assambly,
    orm_get_assambly_all,
    orm_get_page,
    orm_get_pages,
    orm_update_assambly,
    orm_update_logo,
    orm_update_page,
)
from filters.chat_types import ChatTypeFilter, IsAdmin
from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


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


@admin_router.message(Command("admin"))
async def add_page_start(message: types.Message, session: AsyncSession):
    assambly = await orm_get_assambly_all(session)

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



@admin_router.callback_query(StateFilter(None), F.data == "create_assamble")
async def create_assamble(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    await callback.answer("Инструкция создана!")
    await callback.message.answer(
        "Введите название инструкции", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddAssambly.name)


@admin_router.message(F.text == "Просмотреть инструкции")
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


@admin_router.callback_query(F.data.startswith("delete_assambly_"))
async def delete_assambly(callback: types.CallbackQuery, session: AsyncSession):
    assambly_id = callback.data.split("_")[-1]
    await orm_delete_assambly(session, int(assambly_id))

    await callback.answer("Инструкция удалена!")
    await callback.message.answer("Инструкция удалена!")


@admin_router.callback_query(StateFilter(None), F.data.startswith("change_assambly_"))
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


@admin_router.message(StateFilter(None), F.text == "Добавить инструкцию")
async def add_assambly(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название инструкции", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddAssambly.name)


@admin_router.message(StateFilter("*"), Command("отмена"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    if AddAssambly.assambly_for_change:
        AddAssambly.assambly_for_change = None

    if AddPage.page_for_change:
        AddPage.page_for_change = None

    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@admin_router.message(StateFilter(AddAssambly.name), or_f(F.text, F.text == "."))
async def add_assambly_name(message: types.Message, state: FSMContext):
    if message.text == "." and AddAssambly.assambly_for_change:
        await state.update_data(name=AddAssambly.assambly_for_change.name)
    else:
        await state.update_data(name=message.text)

    await message.answer("Введите описание инструкции")
    await state.set_state(AddAssambly.description)


@admin_router.message(StateFilter(AddAssambly.name))
async def add_assambly_name_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте текст!!!")


@admin_router.message(StateFilter(AddAssambly.description), or_f(F.text, F.text == "."))
async def add_assambly_description(message: types.Message, state: FSMContext):
    if message.text == "." and AddAssambly.assambly_for_change:
        await state.update_data(description=AddAssambly.assambly_for_change.description)
    elif message.text == "..":
        await state.update_data(description="")
    else:
        await state.update_data(description=message.text)

    await message.answer("Загрузите изображение")
    await state.set_state(AddAssambly.image)


@admin_router.message(StateFilter(AddAssambly.description))
async def add_assambly_description_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте текст!!!")


@admin_router.message(StateFilter(AddAssambly.image), or_f(F.photo, F.text == "."))
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

    AddPage.page_for_change = None


@admin_router.message(StateFilter(AddAssambly.image))
async def add_image2_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте изображение!!!")

######################### Page ###################################

@admin_router.message(F.text == "Просмотреть")
async def starring_at_page(message: types.Message, session: AsyncSession):
    assambly = await orm_get_assambly_all(session)
    btns = {assambly_item.name: 'view_all_' + str(assambly_item.id) for assambly_item in assambly}
    await message.answer(
        "Выберите инструкцию", reply_markup=get_callback_btns(btns=btns)
    )


@admin_router.callback_query(F.data.startswith('view_all_'))
async def view_pages(callback: types.CallbackQuery, session: AsyncSession):
    assambly_id = callback.data.split('_')[-1]
    pages = await orm_get_pages(session, int(assambly_id))
    
    if pages:
        for page in pages:
            await callback.answer('Запрос получен')
            await callback.message.answer_photo(
                page.image,
                caption=f"<strong>{page.number}\
                        </strong>\n{page.description}",
                reply_markup=get_callback_btns(
                    btns={"Удалить": f"delete_page_{page.id}", "Изменить": f"change_page_{page.id}"}
                ),
            )
    else:
        await callback.answer('Запрос получен')
        await callback.message.answer('В эту инструкцию не добавлено ни одной страницы', reply_markup=ADMIN_KB)


@admin_router.callback_query(F.data.startswith("delete_page_"))
async def delete_page(callback: types.CallbackQuery, session: AsyncSession):
    page_id = callback.data.split("_")[-1]
    await orm_delete_page(session, int(page_id))

    await callback.answer("Лист удален!")
    await callback.message.answer("Лист удален!")


@admin_router.callback_query(StateFilter(None), F.data.startswith("change_page_"))
async def change_page(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    page_id = callback.data.split("_")[-1]
    
    page_for_change = await orm_get_page(session, int(page_id))
    
    AddPage.page_for_change = page_for_change

    assambly = await orm_get_assambly_all(session)
    btns = {assambly_item.name: 'add_page_' + str(assambly_item.id) for assambly_item in assambly}

    await callback.answer("")
    await callback.message.answer(
        "Выберите инструкцию", reply_markup=get_callback_btns(btns=btns)
    )
    await state.set_state(AddPage.assambly)


# Код ниже для машины состояний Page (FSM)


@admin_router.message(StateFilter(None), F.text == "Добавить страницу")
async def add_page_assambly(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    assambly = await orm_get_assambly_all(session)
    btns = {assambly_item.name: 'add_page_' + str(assambly_item.id) for assambly_item in assambly}
    await message.answer(
        "Выберите инструкцию", reply_markup=get_callback_btns(btns=btns)
    )
    await state.set_state(AddPage.assambly)


@admin_router.message(StateFilter("*"), Command("назад"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddPage.number:
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


@admin_router.callback_query(StateFilter(AddPage.assambly), F.data.startswith('add_page_'))
async def add_page_number(callback: types.CallbackQuery, state: FSMContext):
    assambly_id = callback.data.split('_')[-1]
    await state.update_data(assambly=assambly_id)
    await callback.answer("Категория выбрана!")
    await callback.message.answer(
        "Укажите номер листа", reply_markup=types.ReplyKeyboardRemove()
    )

    await state.set_state(AddPage.number)


@admin_router.message(StateFilter(AddPage.number), or_f(F.text, F.text == "."))
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


@admin_router.message(StateFilter(AddPage.number))
async def add_description_error(message: types.Message, state: FSMContext):
    await message.answer(
        "Вы ввели недопустимые данные, отправьте текстом целое число!!!"
    )


@admin_router.message(StateFilter(AddPage.description), or_f(F.text, F.text == "."))
async def add_image(message: types.Message, state: FSMContext):
    if message.text == "." and AddPage.page_for_change:
        await state.update_data(description=AddPage.page_for_change.description)
    elif message.text == "..":
        await state.update_data(description="")
    else:
        await state.update_data(description=message.text)

    await message.answer("Загрузите изображение")
    await state.set_state(AddPage.image)


@admin_router.message(StateFilter(AddPage.description))
async def add_image_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте текст!!!")


@admin_router.message(StateFilter(AddPage.image), or_f(F.photo, F.text == "."))
async def add_image3(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == "." and AddPage.page_for_change:
        await state.update_data(image=AddPage.page_for_change.image)
    elif message.text == '.' and AddPage.page_for_change is None:
        await message.answer('Здесь необходимо отправить изображение!', reply_markup=ADMIN_KB)
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


@admin_router.message(StateFilter(AddPage.image))
async def add_image3_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте изображение!!!")


####### LOGO ######
@admin_router.message(F.text == "Просмотреть лого")
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

@admin_router.message(StateFilter(None), F.text == "Изменить лого")
async def add_logo(message: types.Message, state: FSMContext):
    await message.answer(
        "Отправьте изображение логотипа", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddLogo.image)


@admin_router.message(StateFilter(AddLogo.image), F.photo)
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

@admin_router.message(StateFilter(AddLogo.image))
async def add_image_logo_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте изображение!!!")
