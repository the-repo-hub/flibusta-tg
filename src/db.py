from typing import Callable

from aiogram import BaseMiddleware
from aiogram.types import Update, TelegramObject
from cachetools import LRUCache
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from options import DATABASE_URL

engine = create_async_engine(DATABASE_URL)
Base = declarative_base()
Session = async_sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}
    pk = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)
    username = Column(String(255))
    name = Column(String(255))
    language_code = Column(String(255))
    registered_on = Column(DateTime, nullable=False, default=func.now())

class UserMiddleware(BaseMiddleware):

    def __init__(self, size=1000):
        self.user_cache = LRUCache(maxsize=size)

    async def get_or_create_user(self, event: TelegramObject, session: Session) -> User:
        result = await session.execute(select(User).filter_by(user_id=event.from_user.id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                user_id=event.from_user.id,
                username=event.from_user.username,
                name=event.from_user.full_name,
                language_code=event.from_user.language_code,
            )
            session.add(user)
            session.commit()
        self.user_cache[event.from_user.id] = user
        return user

    async def __call__(self, handler: Callable, update: Update, data):
        event = update.event
        user = self.user_cache.get(event.from_user.id)
        if user is None:
            async with Session() as session:
                await self.get_or_create_user(event, session)
        return await handler(event, data)

async def init_db() -> bool:
    async with engine.begin() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        exists = await conn.run_sync(
            lambda sync_conn: inspector.has_table('users')
        )
        if not exists:
            await conn.run_sync(Base.metadata.create_all)
    return exists
