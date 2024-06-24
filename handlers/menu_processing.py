from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_assambly, orm_get_assambly_all, orm_get_logo, orm_get_pages
from kbds.inline import get_assambly_item_btns, get_page_btns, get_user_assambly_btns, get_user_main_btn
from utils.paginator import Paginator


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns['◀️ Пред'] = 'previous'
    if paginator.has_next():
        btns['▶️ След.'] = 'next'

    return btns

async def main_menu(session, level):
    current_logo = await orm_get_logo(session)
    
    count = 0
    for item in current_logo:
        count += 1
        if count == 1:
            banner = item.image
        else:
            break
    
    image = InputMediaPhoto(media=banner, caption='Привет, я помогу тебе собрать Румбокс!!!')
    kbds = get_user_main_btn(level=level)

    return image, kbds


async def assambly_menu(session, level):
    current_logo = await orm_get_logo(session)
    
    count = 0
    for item in current_logo:
        count += 1
        if count == 1:
            banner = item.image
        else:
            break

    image = InputMediaPhoto(media=banner, caption='Выбери Румбокс')

    assambly = await orm_get_assambly_all(session)

    kbds = get_user_assambly_btns(level=level, assambly=assambly)

    return image, kbds


async def assamble_item_menu(session, level, assambly):
    banner = await orm_get_assambly(session, assambly)
    image = InputMediaPhoto(media=banner.image, caption=f"{banner.name}\n{banner.description}")
    kbds = get_assambly_item_btns(level=level, assambly=banner.id)
    return image, kbds


async def page_menu(session, level, assambly, page):
    
    assambly_pages = await orm_get_pages(session, assambly_id=assambly)

    paginator = Paginator(assambly_pages, page=page)
    current_page = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=current_page.image,
        caption=f'<strong>{current_page.description}\n{paginator.page} из {paginator.pages}</strong>'
    )
    pagination_btns = pages(paginator)

    kbds = get_page_btns(
        level=level,
        assambly=assambly,
        page=page,
        pagination_btns=pagination_btns
    )
    return image, kbds


async def get_menu_content(
        session: AsyncSession,
        level: int,
        # menu_name: str,
        assambly: int | None = None,
        page: int | None = None,
):
    
    if level == 0:
        return await main_menu(session, level)
    elif level == 1:
        return await assambly_menu(session, level)
    elif level == 2:
        return await assamble_item_menu(session, level, assambly)
    elif level ==3:
        return await page_menu(session, level, assambly, page)
    