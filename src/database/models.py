from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Numeric, String, Text, func, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_user_id: Mapped[str] = mapped_column(String, index=True)
    to_group_id: Mapped[str] = mapped_column(String, ForeignKey('groups.group_id'))
    content: Mapped[str] = mapped_column(Text)
    photo_url: Mapped[str] = mapped_column(String, nullable=True)
    document_url: Mapped[str] = mapped_column(String, nullable=True)
    # можно еще добавить в зависимости от задачи
    publish_date: Mapped[DateTime] = mapped_column(DateTime)

    group = relationship("Group", back_populates="messages")

class Group(Base):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(String, index=True)
    group_name: Mapped[str] = mapped_column(String)
    user_id: Mapped[str] = mapped_column(String, index=True)
    username: Mapped[str] = mapped_column(String, index=True)  # для чего нужно?

    messages = relationship("Message", back_populates="group")

class Account(Base):
    __tablename__ = 'accounts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    api_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    api_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True)








