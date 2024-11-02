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