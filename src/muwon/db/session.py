from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from muwon.db.models import Base


def make_session_factory(database_url: str) -> sessionmaker:
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    _add_missing_columns(engine)
    return sessionmaker(bind=engine, class_=Session)


def _add_missing_columns(engine) -> None:
    """create_all()은 없는 테이블만 새로 만들 뿐, 이미 존재하는 테이블에
    나중에 추가된 컬럼은 반영하지 않는다. 이 프로젝트엔 Alembic 같은 별도
    마이그레이션 도구가 없으므로, 최소한 '컬럼 추가'만이라도 자동으로 따라가게
    해서 실거래 데이터가 쌓인 운영 DB가 스키마 변경 한 번에 깨지는 걸 막는다.
    컬럼 삭제·이름 변경·타입 변경처럼 더 복잡한 변경은 다루지 않는다 — 그런
    변경이 필요해지면 Alembic 도입을 검토할 것."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                ddl_type = column.type.compile(engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {ddl_type}'))
