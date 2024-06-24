from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuCallBack(CallbackData, prefix='menu'):
    level: int
    # menu_name: str
    assambly: int | None = None
    page: int = 1



def get_user_main_btn(*, level: int, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        'Начнем': 'start',
    }
    for text, menu_name in btns.items():
        if menu_name == 'start':
            keyboard.add(InlineKeyboardButton(
                text=text, 
                callback_data=MenuCallBack(
                    level=level + 1, 
                    # menu_name=menu_name
                ).pack()
            ))
    return keyboard.adjust(*sizes).as_markup()


def get_user_assambly_btns(*, level: int, assambly: list, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()
    
    for item in assambly:
        keyboard.add(InlineKeyboardButton(
            text=item.name,
            callback_data=MenuCallBack(
                level=level + 1,
                # menu_name=item.name,
                assambly=item.id
            ).pack()
        ))
    
    return keyboard.adjust(*sizes).as_markup()


def get_assambly_item_btns(*, level: int, assambly: int, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data=MenuCallBack(level=level - 1).pack()))
    keyboard.add(InlineKeyboardButton(text='Смотреть', callback_data=MenuCallBack(level=level + 1, assambly=assambly).pack()))
    return keyboard.adjust(*sizes).as_markup()


def get_page_btns(
    *,
    level: int,
    assambly: int,
    page: int,
    pagination_btns: dict,
    sizes: tuple[int] = (1, 2)
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text='Назад',
            callback_data=MenuCallBack(
                level=level - 1,
                assambly=assambly
                # menu_name='start',
            ).pack()
        )
    )
    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == 'next':
            row.append(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=level,
                    # menu_name=menu_name,
                    assambly=assambly,
                    page=page + 1
                ).pack()
            ))
        elif menu_name == 'previous':
            row.append(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=level,
                    # menu_name=menu_name,
                    assambly=assambly,
                    page=page - 1
                ).pack()
            ))
    return keyboard.row(*row).as_markup()



def get_callback_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2, ),
):
    
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


def get_url_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2, ),
):
    
    keyboard = InlineKeyboardBuilder()

    for text, url in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, url=url))

    return keyboard.adjust(*sizes).as_markup()


def get_inline_mix_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2, ),
):
    
    keyboard = InlineKeyboardBuilder()

    for text, value in btns.items():
        if '://' in value:
            keyboard.add(InlineKeyboardButton(text=text, url=value))
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data=value))

    return keyboard.adjust(*sizes).as_markup()
