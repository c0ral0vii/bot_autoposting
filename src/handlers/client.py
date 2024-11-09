from aiogram import Router, types, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
from filters.chat_types import ChatTypeFilter, IsAdmin
from handlers.telethon import get_group_id_from_url
from keyboards.inline.client_kb import create_group_list_keyboard, create_post_list_keyboard, simple_cancel, simple_create_post, simple_post_delete_update, simple_update_post
from keyboards.reply.menu import menu
from fsm.client_fsm import GroupStates
from database.query import add_message, get_account, get_group, get_messages_for_group, get_post, get_post_by_task, get_user_posts, update_account_groups, get_account_groups, delete_post, update_post
from datetime import datetime, timedelta
from src.utils.celery import revoke_task, send_message_task
from src.logger import logger
from celery.result import AsyncResult
from utils.countdown import get_countdown
from utils.validation import is_valid_drive_url, is_valid_group_url, is_valid_time

client_router = Router(name="start")
client_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

@client_router.message(CommandStart())
async def start_handler(message: types.Message) -> None:
    await message.answer('Привет, я бот по автопостингу', reply_markup=menu())


@client_router.callback_query(lambda c: c.data == 'cancel', StateFilter(GroupStates))
async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.message.answer("Вы вернулись в главное меню", reply_markup=menu())

# Мои посты
@client_router.message(F.text == 'Мои посты')
async def my_posts(message: types.Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    posts = await get_user_posts(str(user_id))

    if not posts:
        await message.answer("У вас нет постов.")
        return

    total_posts = len(posts)
    posts_per_page = 5
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    current_page = 1

    page_users = posts[(current_page - 1) * posts_per_page:current_page * posts_per_page]
    keyboard = create_post_list_keyboard(page_users, current_page, total_pages)

    await message.answer("Выберите пост для изменения сообщений:", reply_markup=keyboard)
    await state.set_state(GroupStates.post_page)

@client_router.callback_query(lambda c: c.data.startswith("post_"), StateFilter(GroupStates.post_page))
async def process_select_group(callback_query: types.CallbackQuery, state: FSMContext):
    post_id = callback_query.data.split("_")[1]
    await state.update_data(post_id=str(post_id))

    post = await get_post(str(post_id))

    if post:
        response_text = f"📝 Сообщение #{post.id}\n" \
                        f"ID Группы: {post.to_group_id}\nТекст: {post.content}"
    else:
        response_text = f"Сообщение #{post_id} отсутствуют."

    await callback_query.message.edit_text(response_text, reply_markup=simple_post_delete_update(post))
    await state.set_state(GroupStates.post_page)

@client_router.callback_query(lambda c: c.data.startswith("page_post"), StateFilter(GroupStates.post_page))
async def paginate_post_list(callback_query: types.CallbackQuery, state: FSMContext):
    current_page = int(callback_query.data.split("_")[2])
    user_id = callback_query.from_user.id

    posts = await get_user_posts(str(user_id))
    total_posts = len(posts)
    post_per_page = 5
    total_groups = (total_posts + post_per_page - 1) // post_per_page

    page_posts = posts[(current_page - 1) * post_per_page:current_page * post_per_page]

    keyboard = create_post_list_keyboard(page_posts, current_page, total_groups)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)


# запрос на удаление
@client_router.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_post_handler(callback_query: types.CallbackQuery, state: FSMContext):
    post_id = int(callback_query.data.split("_")[1])

    post = await get_post(post_id)
    if post is None:
        await callback_query.message.answer("Ошибка: пост не найден.")
        return

    task_id = post.celery_id
    if task_id:
        result = revoke_task.apply_async(args=[task_id])  # Запуск задачи для отмены Celery задачи
        if result.get() == f"Task {task_id} has been revoked.":
            await callback_query.message.answer("Задача по отправке сообщения была успешно отменена.")
        else:
            await callback_query.message.answer("Не удалось отменить задачу, возможно, она уже завершена.")


    await delete_post(post_id)

    await callback_query.message.answer("Ваш пост успешно удален ✅")


# запрос на обновление
@client_router.callback_query(lambda c: c.data.startswith("update_"))
async def update_post_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    account = await get_account(user_id)

    api_id = account.api_id
    api_hash = account.api_hash
    phone_number = account.phone_number

    await state.update_data(api_id=api_id, api_hash=api_hash,
                            phone_number=phone_number, user_id=user_id)

    update_post_id = int(callback_query.data.split("_")[1])
    await state.update_data(update_post_id=update_post_id)

    await callback_query.message.answer('Отправь ссылку на канал куда хочешь отправить пост в виде url (https://t.me/chat)',
                                        reply_markup=simple_update_post())
    await state.set_state(GroupStates.group_url)


# пропуск при обновление постов
@client_router.callback_query(lambda c: c.data == "skip_changes")
async def next_step_handler(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()

    next_step = None
    for i, step in enumerate(GroupStates.__all_states__):
        if step.state == current_state:
            if i + 1 < len(GroupStates.__all_states__):
                next_step = GroupStates.__all_states__[i + 1]
                await state.set_state(next_step.state)
                if next_step == "GroupStates:selected_date":
                    await callback_query.message.answer('Выбери дату', reply_markup=await SimpleCalendar(locale=await get_user_locale(callback_query.message.from_user)).start_calendar(is_update=True))
                else:
                    await callback_query.message.answer(f"Ок, вы перешли к следующему шагу \n {GroupStates.texts[str(next_step.state)]}",
                                                        reply_markup=simple_update_post())
            else:
                data = await state.get_data()
                post = await get_post(data["update_post_id"])

                time = data.get('time', post.publish_date.strftime("%H:%M"))
                date = data.get('date', post.publish_date.date())

                countdown = get_countdown(time, date)

                await handle_post_saving(data, countdown, callback_query.message, state, is_update=True)


# Создание поста
@client_router.message(F.text == 'Создать пост')
async def create_post(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id

    account = await get_account(user_id)

    api_id = account.api_id
    api_hash = account.api_hash
    phone_number = account.phone_number

    await state.update_data(api_id=api_id, api_hash=api_hash,
                            phone_number=phone_number, user_id=user_id)

    await message.answer('Отправь ссылку на канал куда хочешь отправить пост в виде url (https://t.me/chat)', reply_markup=simple_cancel())
    await state.set_state(GroupStates.group_url)


@client_router.message(StateFilter(GroupStates.group_url))
async def process_group_url(message: types.Message, state: FSMContext) -> None:
    group_url = message.text.strip()
    data = await state.get_data()
    group_id = await get_group_id_from_url(data["api_hash"], data["api_id"], data["phone_number"], group_url)

    try:
        update_post_id = data["update_post_id"]
    except KeyError:
        update_post_id = None

    if is_valid_group_url(group_url):
        if update_post_id:
            await state.update_data(group_url=group_url, group_id=group_id)
            await message.answer('Выбери дату', reply_markup=await SimpleCalendar(locale=await get_user_locale(message.from_user)).start_calendar(is_update=True))
        else:
            await state.update_data(group_url=group_url, group_id=group_id)
            await message.answer('Выбери дату', reply_markup=await SimpleCalendar(locale=await get_user_locale(message.from_user)).start_calendar())
    else:
        await message.answer('Ссылка на канал неправильная, введи её заново', reply_markup=simple_cancel())


@client_router.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    calendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user), show_alerts=True
    )
    calendar.set_dates_range(datetime.now() - timedelta(days=1), datetime(2030, 12, 31))
    selected, date = await calendar.process_selection(callback_query, callback_data)

    data = await state.get_data()

    try:
        update_post_id = data["update_post_id"]
    except KeyError:
        update_post_id = None

    if selected:
        await state.update_data(date=date)

        if update_post_id:
            await callback_query.message.answer(
                f'Ты выбрал {date.strftime("%d/%m/%Y")}. Теперь выбери время в формате 00:00',
                reply_markup=simple_update_post()
            )
        else:
            await callback_query.message.answer(
                f'Ты выбрал {date.strftime("%d/%m/%Y")}. Теперь выбери время в формате 00:00',
                reply_markup=simple_cancel()
            )
        await state.set_state(GroupStates.time)


@client_router.message(StateFilter(GroupStates.time))
async def process_time(message: types.Message, state: FSMContext) -> None:
    time = message.text.strip()
    data = await state.get_data()

    try:
        update_post_id = data["update_post_id"]
    except KeyError:
        update_post_id = None

    if is_valid_time(time):
        await state.update_data(time=str(time))

        if update_post_id:
            await message.answer('Теперь напиши текст поста', reply_markup=simple_update_post())
        else:
            await message.answer('Теперь напиши текст поста', reply_markup=simple_cancel())
        await state.set_state(GroupStates.text)
    else:
        await message.answer('Неправильный формат времени, попробуй заново (Например 20:00)', reply_markup=simple_cancel())


@client_router.message(StateFilter(GroupStates.text))
async def process_text(message: types.Message, state: FSMContext) -> None:
    content = message.text.strip()
    data = await state.get_data()

    try:
        update_post_id = data["update_post_id"]
    except KeyError:
        update_post_id = None

    await state.update_data(content=content)

    if update_post_id:
        await message.answer('Теперь отправь фото в таком формате "https://drive.google.com/uc?export=download&id={file_id}"', reply_markup=simple_update_post())
    else:
        await message.answer('Теперь отправь фото в таком формате "https://drive.google.com/uc?export=download&id={file_id}"', reply_markup=simple_create_post())

    await state.set_state(GroupStates.photo_url)

@client_router.callback_query(lambda c: c.data == 'skip_media', StateFilter(GroupStates.photo_url))
async def process_skip_photo(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(photo_url=None)

    await callback_query.message.answer('Теперь отправь документ в таком формате "https://drive.google.com/uc?export=download&id={file_id}"', reply_markup=simple_create_post())
    await state.set_state(GroupStates.document_url)

@client_router.message(StateFilter(GroupStates.photo_url))
async def process_photo(message: types.Message, state: FSMContext):
    photo_url = message.text
    data = await state.get_data()

    try:
        update_post_id = data["update_post_id"]
    except KeyError:
        update_post_id = None

    if is_valid_drive_url(photo_url):
        await state.update_data(photo_url=photo_url)

        if update_post_id:
            await message.answer('Теперь отправь документ в таком формате "https://drive.google.com/uc?export=download&id={file_id}"', reply_markup=simple_update_post())
        else:
            await message.answer('Теперь отправь документ в таком формате "https://drive.google.com/uc?export=download&id={file_id}"', reply_markup=simple_create_post())
        await state.set_state(GroupStates.document_url)
    else:
        if update_post_id:
            await message.answer('Неправильный формат, попробуй заново, например (https://drive.google.com/uc?export=download&id=1Rg1OlxvOKmist8RGF41KcuE5VXldda2G)', reply_markup=simple_update_post)
        else:
            await message.answer('Неправильный формат, попробуй заново, например (https://drive.google.com/uc?export=download&id=1Rg1OlxvOKmist8RGF41KcuE5VXldda2G)', reply_markup=simple_create_post())


async def handle_post_saving(data, countdown, message_obj, state, is_update=False):

    if is_update:

        post = await get_post(data["update_post_id"])

        if post is None:
            return

        task_id = post.celery_id

        if task_id:
            result = revoke_task.apply_async(args=[task_id])  # Запуск задачи для отмены Celery задачи
            if result.get() == f"Task {task_id} has been revoked.":
                logger.info("Задача по отправке сообщения была успешно отменена.")

                post = await get_post(data["update_post_id"])
                group = await get_group(post.to_group_id)

                task = send_message_task.apply_async(
                    [data['api_hash'],
                     data['api_id'],
                     data['phone_number'],
                    data.get('group_url', group.group_url),
                    data.get('content', post.content),
                    data.get('photo_url', post.photo_url),
                    data.get('document_url', post.document_url)],
                    countdown=countdown
                )

                time = data.get('time', post.publish_date.strftime("%H:%M"))
                date = data.get('date', post.publish_date.date())
                combined_datetime = datetime.combine(date, datetime.strptime(time, "%H:%M").time())

                await update_post(
                    message_id=data["update_post_id"],
                    group_url=data.get('group_url', None),
                    content=data.get('content', None),
                    photo_url=data.get('photo_url', None),
                    document_url=data.get('document_url', None),
                    publish_date=combined_datetime,
                    celery_id=task.id
                )

                task_id = task.id

                countdown_days = countdown // 86400
                countdown_hours = (countdown % 86400) // 3600
                countdown_minutes = (countdown % 3600) // 60
                countdown_secs = countdown % 60

                post = await get_post_by_task(task_id=task_id)
                group = await get_group(post.to_group_id)

                await message_obj.answer(
                f"✨ **Ваш пост успешно сохранен!**\n\n"
                f"📅 **Дата:** {post.publish_date.strftime('%Y-%m-%d')}\n"
                f"⏰ **Время:** {post.publish_date.strftime('%H:%M')}\n"
                f"📛 **Название группы:** {group.group_name}\n"
                f"💬 **Сообщение:** {post.content}\n\n"
                f"⏳ **Будет отправлено через:**\n"
                f"{countdown_days} дней, {countdown_hours} часов, {countdown_minutes} минут, {countdown_secs} секунд\n",
                parse_mode="Markdown",
                reply_markup=menu()
                )

            else:
                await logger.warning("Не удалось отменить задачу, возможно, она уже завершена.")

    else:
        combined_datetime = datetime.combine(data['date'].date(), datetime.strptime(data['time'], "%H:%M").time())

        task = send_message_task.apply_async(
            [data['api_hash'], data['api_id'], data['phone_number'],
                data['group_url'], data['content'], data['photo_url'], data['document_url']],
            countdown=countdown
        )

        task_id = task.id

        await add_message(data['user_id'], data['group_id'], data['content'],
                            data['photo_url'], data['document_url'], str(task.id), combined_datetime)

        countdown_days = countdown // 86400
        countdown_hours = (countdown % 86400) // 3600
        countdown_minutes = (countdown % 3600) // 60
        countdown_secs = countdown % 60

        post = await get_post_by_task(task_id=task_id)
        group = await get_group(post.to_group_id)

        await message_obj.answer(
        f"✨ **Ваш пост успешно сохранен!**\n\n"
        f"📅 **Дата:** {post.publish_date.strftime('%Y-%m-%d')}\n"
        f"⏰ **Время:** {post.publish_date.strftime('%H:%M')}\n"
        f"📛 **Название группы:** {group.group_name}\n"
        f"💬 **Сообщение:** {post.content}\n\n"
        f"⏳ **Будет отправлено через:**\n"
        f"{countdown_days} дней, {countdown_hours} часов, {countdown_minutes} минут, {countdown_secs} секунд\n",
        parse_mode="Markdown",
        reply_markup=menu()
        )

    await state.clear()


@client_router.callback_query(lambda c: c.data == 'skip_media', StateFilter(GroupStates.document_url))
async def process_document_skip(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(document_url=None)
    data = await state.get_data()

    countdown = get_countdown(data['time'], data['date'])

    await handle_post_saving(data, countdown, callback_query.message, state)


@client_router.message(StateFilter(GroupStates.document_url))
async def process_document(message: types.Message, state: FSMContext):
    document_url = message.text

    if is_valid_drive_url(document_url):
        await state.update_data(document_url=document_url)
        data = await state.get_data()

        try:
            update_post_id = data["update_post_id"]
        except:
            update_post_id = None

        countdown = get_countdown(data['time'], data['date'])

        if update_post_id:
            await handle_post_saving(data, countdown, message, state, is_update=True)
        else:
            await handle_post_saving(data, countdown, message, state)
    else:
        await message.answer('Неправильный формат, попробуй заново, например (https://drive.google.com/uc?export=download&id=1Rg1OlxvOKmist8RGF41KcuE5VXldda2G)')


# Обновить группы
@client_router.message(F.text == 'Обновить группы')
async def update_groups_handler(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    try:
        await update_account_groups(user_id)
        await message.answer("Ваши группы обновлены ✅")
    except:
        await message.answer("Произошла ошибка ❌")


# Группы пользователя
@client_router.message(F.text == 'Мои группы')
async def my_groups_handler(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    groups = await get_account_groups(str(user_id))
    total_groups = len(groups)
    groups_per_page = 5
    total_pages = (total_groups + groups_per_page - 1) // groups_per_page
    current_page = 1

    page_users = groups[(current_page - 1) * groups_per_page:current_page * groups_per_page]
    keyboard = create_group_list_keyboard(page_users, current_page, total_pages)

    await message.answer("Выберите группу для просмотра постов:", reply_markup=keyboard)
    await state.set_state(GroupStates.group_page)

@client_router.callback_query(lambda c: c.data.startswith("group_"), StateFilter(GroupStates.group_page))
async def process_select_group(callback_query: types.CallbackQuery, state: FSMContext):
    group_id = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id

    posts = await get_messages_for_group(str(user_id), str(group_id))
    group = await get_group(str(group_id))

    total_posts = len(posts)
    posts_per_page = 5
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    current_page = 1

    page_users = posts[(current_page - 1) * posts_per_page:current_page * posts_per_page]
    keyboard = create_post_list_keyboard(page_users, current_page, total_pages)

    if posts:
        await callback_query.message.answer("Выбери пост для изменения", reply_markup=keyboard)
        await state.set_state(GroupStates.post_page)
    else:
        await callback_query.message.answer("Сообщения для данной группы отсутствуют", reply_markup=simple_cancel())
        await state.set_state(GroupStates.group_page)

@client_router.callback_query(lambda c: c.data.startswith("page_"), StateFilter(GroupStates.group_page))
async def paginate_user_list(callback_query: types.CallbackQuery, state: FSMContext):
    current_page = int(callback_query.data.split("_")[1])

    user_id = callback_query.from_user.id
    groups = await get_account_groups(str(user_id))
    total_groups = len(groups)
    group_per_page = 5
    total_groups = (total_groups + group_per_page - 1) // group_per_page

    page_groups = groups[(current_page - 1) * group_per_page:current_page * group_per_page]

    keyboard = create_group_list_keyboard(page_groups, current_page, total_groups)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)




