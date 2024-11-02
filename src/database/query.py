from datetime import datetime
from database.settings import async_session
from sqlalchemy import delete, insert, select, cast
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from database.models import *
from logger import logger
from handlers.telethon import telethon_get_account_groups
from typing import Optional


async def get_account(user_id: str):
    async with async_session() as session:
        try:
            stmt = select(Account).where(Account.user_id == str(user_id))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user is None:
                raise NoResultFound(f"No user found with user_id: {user_id}")
            return user
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


from sqlalchemy import or_

async def get_group(group_id: str):
    async with async_session() as session:
        try:
            if group_id.startswith("-100"):
                normal_group_id = group_id.replace("-100", "", 1)
                stmt = select(Group).where(
                    or_(
                        Group.group_id == str(group_id),
                        Group.group_id == str(normal_group_id)
                    )
                )
            else:
                supergroup_id = f"-100{abs(int(group_id))}"
                stmt = select(Group).where(
                    or_(
                        Group.group_id == str(group_id),
                        Group.group_id == str(supergroup_id)
                    )
                )
            result = await session.execute(stmt)
            group = result.scalar_one_or_none()
            if group is None:
                raise NoResultFound(f"No group found with group_id: {group_id}")
            return group
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            return None



async def update_account_groups(user_id: str):
    async with async_session() as session:
        try:
            await delete_account_groups(str(user_id))
        except:
            logger.warning('Deleting not completed')

        account = await get_account(str(user_id))
        groups = await telethon_get_account_groups(account.api_hash, account.api_id, account.phone_number)

        for group_id, group_name in groups:
            new_group = Group(
                group_id=str(group_id),
                group_name=group_name,
                user_id=str(user_id),
                username=f"username"
            )
            session.add(new_group)
        await session.commit()


async def get_account_groups(user_id: str):
    async with async_session() as session:
        stmt = select(Group).filter_by(user_id=user_id)
        response = await session.execute(stmt)
        groups = response.scalars().all()
        return groups


async def delete_account_groups(user_id: str):
    async with async_session() as session:
        try:
            stmt = delete(Group).filter_by(user_id=user_id)
            await session.execute(stmt)
            await session.commit()
        except SQLAlchemyError as e:
            logger.warning(f'Error: {e}')


async def get_messages_for_group(user_id: str, group_id: str):
    async with async_session() as session:
        try:
            # Проверка, начинается ли group_id с префикса супергруппы "-100"
            if group_id.startswith("-100"):
                supergroup_id = group_id  # Исходный идентификатор супергруппы
                normal_group_id = group_id.replace("-100", "", 1)  # Идентификатор без префикса
            else:
                normal_group_id = group_id  # Исходный идентификатор
                supergroup_id = f"-100{abs(int(group_id))}"  # Идентификатор с префиксом "-100"

            stmt = select(Message).filter(
                Message.from_user_id == user_id,
                (Message.to_group_id == normal_group_id) | (Message.to_group_id == supergroup_id)
            )

            result = await session.execute(stmt)
            messages = result.scalars().all()

            logger.info(f"Fetched {len(messages)} messages for user_id: {user_id} and group_id: {group_id}")
            return messages
        except NoResultFound:
            logger.warning(f"No messages found for user_id: {user_id} and group_id: {group_id}")
            return []
        except Exception as e:
            logger.error(f"An error occurred while fetching messages: {e}")
            return []


async def add_message(user_id: str, group_url: str, content: str,
                      photo_url: Optional[str], document: Optional[str], publish_date: datetime):
    async with async_session() as session:
        try:
            stmt = insert(Message).values(
                from_user_id=str(user_id),
                to_group_id=str(group_url),
                content=content,
                photo_url=photo_url if photo_url else None,
                document_url=document if document else None,
                publish_date=publish_date
            )
            await session.execute(stmt)
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"An error occurred: {e}")


async def get_user_posts(user_id: str):
    async with async_session() as session:
        try:
            stmt = select(Message).filter_by(from_user_id=user_id)
            response = await session.execute(stmt)
            posts = response.scalars().all()
            return posts
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"An error occurred: {e}")


async def get_post(post_id: str):
    async with async_session() as session:
        try:
            stmt = select(Message).filter_by(id=int(post_id))
            response = await session.execute(stmt)
            post = response.scalar_one_or_none()
            return post
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"An error occurred: {e}")






