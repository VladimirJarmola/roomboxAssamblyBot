from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from filters.chat_types import ChatTypeFilter, IsAdmin
from kbds.reply import get_keyboard


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(['private']), IsAdmin())


ADMIN_KB = get_keyboard(
    "Добавить страницу",
    "Изменить страницу",
    "Удалить страницу",
    "Я так, просто проверить зашел",
    placeholder="Выберите действие",
    sizes=(2, 1, 1),
)


@admin_router.message(Command("admin"))
async def add_list_start(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)

# ДЛЯ БАЗЫ ДАНЫХ
# @admin_router.message(F.text == "Я так, просто посмотреть зашел")
# async def starring_at_list(message: types.Message):
#     await message.answer("ОК, вот список листов")


# @admin_router.message(F.text == "Изменить лист")
# async def change_list(message: types.Message):
#     await message.answer("ОК, вот список листов")


# @admin_router.message(F.text == "Удалить лист")
# async def delete_list(message: types.Message):
#     await message.answer("Выберите лист(ы) для удаления")


#Код ниже для машины состояний (FSM)
    
class AddList(StatesGroup):
    number = State()
    description = State()
    image = State()

    texts = {
        'AddList:number': 'Введите номер заново',
        'AddList:description': 'Введите описание заново',
        'AddList:image': 'Это последний стэйт ... ',
    }



@admin_router.message(StateFilter(None), F.text == "Добавить страницу")
async def add_list_number(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите номер инструкции", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddList.number)


@admin_router.message(StateFilter('*'), Command("отмена"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state() 
    if current_state is None:
        return
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@admin_router.message(StateFilter('*'), Command("назад"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "назад")
async def back_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state() 

    if current_state == AddList.number:
        await message.answer(f'Предыдущего шага нет,\nили введите номер страницы,\nили введите "отмена"')
        return

    previous = None
    for step in AddList.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"ок, вы вернулись к предыдущему шагу \n {AddList.texts[previous.state]}")
            return
        previous = step


@admin_router.message(StateFilter(AddList.number), F.text)
async def add_description(message: types.Message, state: FSMContext):
    await state.update_data(number=message.text)
    await message.answer("Введите описание листа инструкции")
    await state.set_state(AddList.description)


@admin_router.message(StateFilter(AddList.number))
async def add_description_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте текстом целое число!!!")


@admin_router.message(StateFilter(AddList.description), F.text)
async def add_image(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Загрузите изображение")
    await state.set_state(AddList.image)


@admin_router.message(StateFilter(AddList.description))
async def add_image_error(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте текст!!!")


@admin_router.message(StateFilter(AddList.image), F.photo)
async def add_image2(message: types.Message, state: FSMContext):
    await state.update_data(image=message.photo[-1].file_id)
    await message.answer("Лист инструкции добавлен", reply_markup=ADMIN_KB)
    data = await state.get_data()
    await message.answer(str(data))
    await state.clear()


@admin_router.message(StateFilter(AddList.image))
async def add_image_уккщк(message: types.Message, state: FSMContext):
    await message.answer("Вы ввели недопустимые данные, отправьте изображение!!!")
