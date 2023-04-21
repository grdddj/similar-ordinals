import json
from pathlib import Path

from common import get_logger
from config import Config
from db_similarity_index import SimilarityIndex, get_highest_id, get_session
from get_matches import get_matches_from_data
from rust_server import get_matches_from_rust_server

HERE = Path(__file__).parent

log_file_path = HERE / "update_similarity_index.log"
logger = get_logger(__file__, log_file_path)

is_rust_server_running = True
try:
    get_matches_from_rust_server(ord_id=1, file_hash=None)
    logger.info("Rust server is running")
except Exception as e:
    is_rust_server_running = False
    logger.error(f"Rust server is not running {e}")


def main():
    highest_indexed_id = get_highest_id()
    logger.info(f"highest_indexed_id {highest_indexed_id}")

    with open(Config.AVERAGE_HASH_DB, "r") as f:
        data = json.load(f)["data"]

    already_indexed_data: dict[str, str] = {
        k: v for k, v in data.items() if int(k) <= highest_indexed_id
    }
    not_indexed_data: dict[str, str] = {
        k: v for k, v in data.items() if int(k) > highest_indexed_id
    }

    session = get_session()

    # calculate the index for all the ord_ids higher than highest_indexed_id
    for progress, (ord_id, average_hash) in enumerate(not_indexed_data.items()):
        if progress % 100 == 0:
            logger.info(f"New update progress {progress} / {len(not_indexed_data)}")
        if session.query(SimilarityIndex).get(int(ord_id)) is not None:
            continue
        if is_rust_server_running:
            matches = get_matches_from_rust_server(ord_id=None, file_hash=average_hash)
        else:
            matches = get_matches_from_data(
                data, ord_id=None, file_hash=average_hash, top_n=20
            )
        list_of_lists = [
            [int(match["ord_id"]), match["match_sum"]] for match in matches
        ]
        obj = SimilarityIndex(
            id=int(ord_id),
            list_of_lists=json.dumps(list_of_lists),
        )
        session.add(obj)
        if progress % 100 == 0:
            session.commit()

    # calculate the similarities for older ones - but just with new ones
    for progress, (old_ord_id, old_average_hash) in enumerate(
        already_indexed_data.items()
    ):
        if progress % 100 == 0:
            logger.info(f"Old update progress {progress} / {len(already_indexed_data)}")
        new_matches = get_matches_from_data(
            not_indexed_data, ord_id=None, file_hash=old_average_hash, top_n=20
        )
        old_matches = SimilarityIndex.list_by_id(int(old_ord_id))

        new_matches_old_format = [
            [int(match["ord_id"]), match["match_sum"]] for match in new_matches
        ]
        all_matches_together = old_matches + new_matches_old_format
        all_matches_together.sort(key=lambda x: x[1], reverse=True)
        new_top_matches = all_matches_together[:20]
        if old_matches == new_top_matches:
            continue
        obj = session.query(SimilarityIndex).get(int(old_ord_id))
        if obj is None:
            continue
        obj.list_of_lists = json.dumps(new_top_matches)
        if progress % 100 == 0:
            session.commit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
