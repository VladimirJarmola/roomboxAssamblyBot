from aiogram import Router, types, F
from aiogram.filters import CommandStart


user_private_router  = Router()


@user_private_router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer('Hello')


@user_private_router.message(F.text)
async def any_text(message: types.Message):
    await message.answer(message.text)
    