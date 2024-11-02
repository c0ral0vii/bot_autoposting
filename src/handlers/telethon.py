import os
import requests
from io import BytesIO
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError, ChannelPrivateError, UserAlreadyParticipantError
from telethon.tl.functions.channels import JoinChannelRequest
from src.logger import logger


async def telethon_get_account_groups(api_hash: str, api_id: str, phone_number: str):
    session_name = f'session_{phone_number.replace("+", "")}.session'
    session_path = os.path.join('sessions', session_name)

    async with TelegramClient(session_path, api_id, api_hash) as client:
        try:
            await client.start(phone=phone_number)
            dialogs = await client.get_dialogs()
            groups = [
                (dialog.id, dialog.title)
                for dialog in dialogs
                if dialog.is_group or dialog.is_channel
            ]
            return groups

        except SessionPasswordNeededError:
            logger.warning("Two-step verification is enabled. Please provide the password.")
        except FloodWaitError as e:
            logger.warning(f"You are being rate-limited. Please wait {e.seconds} seconds.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

async def telethon_send_message(api_hash: str, api_id: str, phone_number: str, group_url: str, content: str, photo_url: str, document_url: str):
    session_name = f'session_{phone_number.replace("+", "")}.session'
    session_path = os.path.join('sessions', session_name)

    async with TelegramClient(session_path, api_id, api_hash) as client:
        try:
            await client.start(phone=phone_number)

            try:
                group_entity = await client.get_entity(group_url)
            except ChannelPrivateError:
                logger.error("The group is private, and you don't have access.")
                return

            try:
                await client(JoinChannelRequest(group_entity))
                logger.info(f"Successfully joined the group: {group_url}")
            except UserAlreadyParticipantError:
                logger.info(f"Already a participant in {group_url}")


            if photo_url is not None:
                await client.send_file(group_entity, photo_url, caption=content)
                logger.info(f"Photo sent to group {group_url}: {photo_url}")

            if document_url is not None:
                response = requests.get(document_url)
                file_stream = BytesIO(response.content)
                file_stream.name = "document.pdf"
                await client.send_file(group_entity, file_stream, caption=content)
                logger.info(f"Document sent to group {group_url}: {document_url}")

            if not photo_url and not document_url:
                await client.send_message(group_entity, content)
                logger.info(f"Message sent to group {group_url}: {content}")

        except SessionPasswordNeededError:
            print("Two-step verification is enabled. Please provide the password.")
        except FloodWaitError as e:
            print(f"You are being rate-limited. Please wait {e.seconds} seconds.")
        except Exception as e:
            print(f"An error occurred: {e}")

async def get_group_id_from_url(api_hash: str, api_id: str, phone_number: str, group_url: str):
    session_name = f'session_{phone_number.replace("+", "")}.session'
    session_path = os.path.join('sessions', session_name)

    async with TelegramClient(session_path, api_id, api_hash) as client:
        try:
            await client.start(phone=phone_number)
            username = group_url.split('/')[-1]
            group = await client.get_entity(username)
            return f"-{group.id}"

        except SessionPasswordNeededError:
            logger.warning("Two-step verification is enabled. Please provide the password.")
        except FloodWaitError as e:
            logger.warning(f"You are being rate-limited. Please wait {e.seconds} seconds.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None


