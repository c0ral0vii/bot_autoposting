from datetime import datetime, timedelta

from datetime import datetime, timedelta

def get_countdown(time: str, date: datetime) -> int:
    # Преобразуем строку времени в объект time
    target_time = datetime.strptime(time, "%H:%M").time()

    # Если date - это datetime (с временной частью), берем только date
    if isinstance(date, datetime):
        target_datetime = datetime.combine(date.date(), target_time)
    elif isinstance(date, timedelta):
        # Если передан timedelta, то сразу комбинируем его с датой
        target_datetime = datetime.combine(date.date(), target_time)
    else:
        # Если передан только date (без времени)
        target_datetime = datetime.combine(date, target_time)

    # Если целевое время уже прошло, увеличиваем на один день
    if target_datetime < datetime.now():
        target_datetime += timedelta(days=1)

    # Вычисляем разницу во времени
    now = datetime.now()
    countdown = target_datetime - now

    return int(countdown.total_seconds())
