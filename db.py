from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
from aiogram.types import User as UserType, Message
import functools

engine = create_engine("postgresql+psycopg2://flibusta_tg:secret@localhost:5432/flibusta_tg")

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'public'}
    pk = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)
    username = Column(String(255))
    name = Column(String(255))
    request = Column(String(255))
    language_code = Column(String(255))
    registered_on = Column(DateTime, nullable=False, default=func.now())
    last_request = Column(DateTime, nullable=False, default=func.now())

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def user_db_wrapper(fn):
    @functools.wraps(fn)
    async def wrapper(msg: Message):
        session = Session()
        tg_user: UserType = msg.from_user
        user = session.query(User).filter_by(user_id=tg_user.id).first()
        if not user:
            user = User(
                user_id=tg_user.id,
                username=tg_user.username,
                name=tg_user.full_name,
                request=msg.text,
                language_code=tg_user.language_code,
            )
            session.add(user)
        else:
            user.last_request = func.now()
            user.request = msg.text
        session.commit()
        return await fn(msg)
    return wrapper