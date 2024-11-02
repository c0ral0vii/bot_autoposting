import re
from datetime import datetime

def is_valid_group_url(url: str) -> bool:
    pattern = r"^(https?://)?t\.me/[a-zA-Z0-9_]+$"
    return bool(re.match(pattern, url))

def is_valid_time(time_str: str) -> bool:
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def is_valid_drive_url(photo_url: str) -> bool:
    pattern = r"^https:\/\/drive\.google\.com\/uc\?export=download&id=[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, photo_url))
