from __future__ import annotations

import json

from sqlmodel import Field, Session, SQLModel, create_engine

from config import Config


def get_session() -> Session:
    engine = get_engine()
    return Session(engine)


def get_engine():
    return create_engine(f"sqlite:///{Config.SIMILARITY_INDEX_DB}", echo=False)


class SimilarityIndex(SQLModel, table=True):
    __tablename__ = "similarity_index"

    id: int = Field(primary_key=True)
    list_of_lists: str = Field(nullable=False)

    @classmethod
    def is_defined(cls, id: int) -> bool:
        with get_session() as session:
            return session.query(SimilarityIndex).get(id) is not None

    @classmethod
    def list_by_id(cls, id: int) -> list[list[int]]:
        with get_session() as session:
            obj = (
                session.query(SimilarityIndex).filter(SimilarityIndex.id == id).first()
            )
            if obj is None:
                return []
            return json.loads(obj.list_of_lists)

    @classmethod
    def save_new(cls, id: int, list_of_lists: list[list[int]]) -> None:
        with get_session() as session:
            # not doing anything, if already there
            if session.query(SimilarityIndex).get(id) is not None:
                return
            obj = SimilarityIndex(
                id=id,
                list_of_lists=json.dumps(list_of_lists),
            )
            session.add(obj)
            session.commit()

    @classmethod
    def update_old(cls, id: int, list_of_lists: list[list[int]]) -> None:
        with get_session() as session:
            obj = session.query(SimilarityIndex).get(id)
            if obj is None:
                return
            obj.list_of_lists = json.dumps(list_of_lists)
            session.commit()


def get_highest_id() -> int:
    with get_session() as session:
        result = (
            session.query(SimilarityIndex).order_by(SimilarityIndex.id.desc()).first()  # type: ignore
        )
        return int(result.id) if result else 0


if __name__ == "__main__":
    # Create the table in the database
    SQLModel.metadata.create_all(get_engine())
