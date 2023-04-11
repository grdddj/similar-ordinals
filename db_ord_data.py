from typing import Iterator

from sqlmodel import Field, Index, Session, SQLModel, UniqueConstraint, create_engine
from typing_extensions import Self

db_location = "ord_data.db"


def get_session() -> Session:
    engine = get_engine()
    return Session(engine)


def get_engine():
    return create_engine(f"sqlite:///{db_location}", echo=False)


class InscriptionModel(SQLModel, table=True):
    __tablename__ = "inscriptions"

    id: int = Field(primary_key=True)
    tx_id: str = Field(nullable=False)
    minted_address: str = Field(nullable=False)
    content_type: str = Field(nullable=False)
    content_hash: str = Field(nullable=False)
    datetime: str = Field(nullable=False)
    timestamp: int = Field(nullable=False)
    content_length: int = Field(nullable=False)
    genesis_fee: int = Field(nullable=False)
    genesis_height: int = Field(nullable=False)
    output_value: int = Field(nullable=False)

    __table_args__ = (
        UniqueConstraint("tx_id", name="uq_tx_id"),  # secondary key to tx_id
        Index("ix_inscriptions_id", "id", unique=True),  # for bulk inserts to work
    )

    def __repr__(self) -> str:
        return f"<Inscription({self.id}, {self.tx_id}, {self.content_type}, {self.content_length:_})>"

    def __str__(self) -> str:
        return self.__repr__()

    def tx_id_ellipsis(self) -> str:
        return f"{self.tx_id[:4]}...{self.tx_id[-4:]}"

    def ordinals_com_link(self) -> str:
        return f"https://ordinals.com/inscription/{self.tx_id}i0"

    def ordinals_com_content_link(self) -> str:
        return f"https://ordinals.com/content/{self.tx_id}i0"

    def mempool_space_link(self) -> str:
        return f"https://mempool.space/tx/{self.tx_id}"

    @classmethod
    def by_tx_id(cls, tx_id: str) -> Self:
        session = get_session()
        return (
            session.query(InscriptionModel)
            .filter(InscriptionModel.tx_id == tx_id)
            .first()
        )

    @classmethod
    def by_id(cls, id: int) -> Self:
        session = get_session()
        return session.query(InscriptionModel).filter(InscriptionModel.id == id).first()


def get_all_image_inscriptions_iter() -> Iterator[InscriptionModel]:
    session = get_session()
    yield from session.query(InscriptionModel).filter(
        InscriptionModel.content_type.like("image/%")
    ).yield_per(100)


if __name__ == "__main__":
    # Create the table in the database
    SQLModel.metadata.create_all(get_engine())
