from aiogram import F, Router, types
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from filters.chat_types import ChatTypeFilter
from handlers.menu_processing import get_menu_content
from kbds.inline import MenuCallBack


user_private_router  = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))


@user_private_router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    media, reply_markup = await get_menu_content(session, level=0)

    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup, protect_content=True)


@user_private_router.callback_query(MenuCallBack.filter())
async def assambly_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):
    media, reply_markup = await get_menu_content(
        session, 
        level=callback_data.level, 
        # menu_name=callback_data.menu_name,
        assambly=callback_data.assambly,
        page=callback_data.page,
    )
    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()
