from pathlib import Path

HERE = Path(__file__).parent


class Config:
    FILE_DB = HERE / "ord_files.db"
    ORD_DB = HERE / "ord.db"
    SIMILARITY_INDEX_DB = HERE / "similarity_index.db"
    HASH_SIZE = 16
    AVERAGE_HASH_DB = HERE / f"average_hash_db_{HASH_SIZE}.json"
    RUST_API_URL = "http://localhost:8081"
    RUST_LIB_PATH = HERE / "similar_pictures/target/release/libsimilar_pictures.so"
