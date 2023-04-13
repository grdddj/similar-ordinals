from __future__ import annotations

from sqlmodel import Field, Index, Session, SQLModel, create_engine

db_location = "ord_files.db"
db_location = "/mnt/c/Users/musil/Downloads/ord_content_data.db"


def get_session() -> Session:
    engine = get_engine()
    return Session(engine)


def get_engine():
    return create_engine(f"sqlite:///{db_location}", echo=False)


class ByteData(SQLModel, table=True):
    __tablename__ = "byte_data"

    id: str = Field(primary_key=True)
    data: bytes = Field(nullable=False)

    __table_args__ = (
        # for bulk inserts to work
        Index("ix_byte_data_id", "id", unique=True),
    )


def get_data(tx_id: str) -> bytes | None:
    session = get_session()
    try:
        result = session.query(ByteData).get(tx_id)
        return result.data if result else None
    finally:
        session.close()


if __name__ == "__main__":
    # Create the table in the database
    SQLModel.metadata.create_all(get_engine())
