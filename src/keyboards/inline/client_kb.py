from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def create_group_list_keyboard(groups, page: int = 1, total_pages: int = 1):
    group_buttons = [
        [InlineKeyboardButton(text=f"{group.group_name}", callback_data=f"group_{group.group_id}")]
        for group in groups
    ]

    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))

    cancel_button = InlineKeyboardButton(text="Отмена", callback_data="cancel")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        *group_buttons,
        navigation_buttons,
        [cancel_button]
    ])

    return keyboard

def create_post_list_keyboard(posts, page: int = 1, total_pages: int = 1):
    post_buttons = [
        [InlineKeyboardButton(text=f"{post.id} {post.content}", callback_data=f"post_{post.id}")]
        for post in posts
    ]

    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_post_{page - 1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton(text="➡️ Следующий", callback_data=f"page_post_{page + 1}"))

    cancel_button = InlineKeyboardButton(text="Отмена", callback_data="cancel")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        *post_buttons,
        navigation_buttons,
        [cancel_button]
    ])

    return keyboard

def simple_create_post():
    skip_button = InlineKeyboardButton(text="Пропустить", callback_data="skip")
    cancel_button = InlineKeyboardButton(text="Отмена", callback_data="cancel")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [skip_button, cancel_button]
    ])

    return keyboard

def simple_cancel():
    cancel_button = InlineKeyboardButton(text="Отмена", callback_data="cancel")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [cancel_button]
    ])

    return keyboard