from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def menu():
    create_post = KeyboardButton(text="Создать пост")
    my_posts = KeyboardButton(text="Мои посты")
    my_groups = KeyboardButton(text="Мои группы")
    update_groups = KeyboardButton(text="Обновить группы")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [create_post, my_posts],
            [my_groups, update_groups]
        ],
        resize_keyboard=True
    )

    return keyboard