from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from muwon.db.models import Base


def make_session_factory(database_url: str) -> sessionmaker:
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, class_=Session)
