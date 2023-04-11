from __future__ import annotations

import json

from sqlmodel import Field, Session, SQLModel, create_engine

db_location = "similarity_index.db"


def get_session() -> Session:
    engine = get_engine()
    return Session(engine)


def get_engine():
    return create_engine(f"sqlite:///{db_location}", echo=False)


class SimilarityIndex(SQLModel, table=True):
    __tablename__ = "similarity_index"

    id: str = Field(primary_key=True)
    list_of_lists: str = Field(nullable=False)

    @classmethod
    def list_by_id(cls, id: int) -> list[list[int]]:
        session = get_session()
        object = session.query(SimilarityIndex).filter(SimilarityIndex.id == id).first()
        if object is None:
            return []
        return json.loads(object.list_of_lists)


if __name__ == "__main__":
    # Create the table in the database
    SQLModel.metadata.create_all(get_engine())
