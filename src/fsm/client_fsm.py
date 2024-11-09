from aiogram.fsm.state import State, StatesGroup

class GroupStates(StatesGroup):
    group_page = State()
    post_page = State()
    group_url = State()
    selected_date = State()
    time = State()
    text = State()
    photo_url = State()
    document_url = State()

    texts = {
        "GroupStates:group_page": "Пожалуйста, выберите группу.",
        "GroupStates:post_page": "Вы на странице поста. Что вы хотите сделать?",
        "GroupStates:group_url": "Введите URL группы.",
        "GroupStates:selected_date": "Выберите дату.",
        "GroupStates:time": "Укажите время.",
        "GroupStates:text": "Введите текст сообщения.",
        "GroupStates:photo_url": "Добавьте ссылку на фото.",
        "GroupStates:document_url": "Добавьте ссылку на документ."
    }