import asyncio
from celery import Celery
from src.handlers.telethon import telethon_send_message

celery_app = Celery(
    'celery',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.update(
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task
def send_message_task(api_hash: str, api_id: str, phone_number: str, group_url: str, content: str, photo_url: str, document_url: str):
    asyncio.run(telethon_send_message(api_hash, api_id, phone_number, group_url, content, photo_url, document_url))

