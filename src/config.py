from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

BOT_TOKEN=str(os.environ.get("BOT_TOKEN"))
DB_HOST=str(os.environ.get("DB_HOST"))
DB_USER=str(os.environ.get("DB_USER"))
DB_PASS=str(os.environ.get("DB_PASS"))
DB_PORT=str(os.environ.get("DB_PORT"))
DB_NAME=str(os.environ.get("DB_NAME"))
ADMINS_LIST = os.environ.get("ADMINS_LIST", "")
ADMINS_LIST = [
    int(admin.split("#")[0].strip()) for admin in ADMINS_LIST.split(",") if admin.split("#")[0].strip().isdigit()
]
