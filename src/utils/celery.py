import asyncio
from celery import Celery
from src.handlers.telethon import telethon_send_message
from celery.result import AsyncResult

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

@celery_app.task
def revoke_task(task_id: str):
    """Revoke a Celery task by its task_id if it is still active."""
    task = AsyncResult(task_id)
    if task.state not in ['SUCCESS', 'FAILURE', 'REVOKED']:  # Check if the task is not already completed or revoked
        task.revoke(terminate=True)  # Terminate=True forces the task to stop
        return f"Task {task_id} has been revoked."
    return f"Task {task_id} is already in state {task.state}."

