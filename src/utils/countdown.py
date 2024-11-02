from datetime import datetime, timedelta

def get_countdown(time: str, date: datetime) -> int:
    target_time = datetime.strptime(time, "%H:%M").time()
    target_datetime = datetime.combine(date.date(), target_time)

    if target_datetime < datetime.now():
        target_datetime += timedelta(days=1)

    now = datetime.now()
    countdown = target_datetime - now

    return int(countdown.total_seconds())