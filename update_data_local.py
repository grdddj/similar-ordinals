from __future__ import annotations

import json
from pathlib import Path

from common import bytes_to_hash, get_logger
from config import Config
from db_files import get_data
from db_ord_data import get_all_image_inscriptions_iter_bigger_than

HERE = Path(__file__).parent

log_file_path = HERE / "update_data_local.log"
logger = get_logger(__file__, log_file_path)

new_hashes_file = HERE / "new_average_hashes_local.txt"

new_average_hashes: dict[str, str] = {}


def get_current_data() -> dict[str, str]:
    with open(Config.AVERAGE_HASH_DB) as f:
        return json.load(f)["data"]


def save_new_data(new_data: dict[str, str]) -> None:
    with open(Config.AVERAGE_HASH_DB, "w") as f:
        results = {"data": new_data}
        json.dump(results, f, indent=1)


def get_our_last_id(data: dict[str, str]) -> int:
    return max(int(k) for k in data.keys())


def save_new_avg_hash(ord_id: str, avg_hash: str) -> None:
    with open(new_hashes_file, "a") as f:
        f.write(f"{ord_id} {avg_hash}\n")


def main() -> None:
    average_hash_data = get_current_data()
    last_id = get_our_last_id(average_hash_data)

    for progress, inscr in enumerate(
        get_all_image_inscriptions_iter_bigger_than(last_id)
    ):
        if progress % 100 == 0:
            logger.info(f"Progress {progress}")
        ord_id = inscr.id
        try:
            content = get_data(inscr.tx_id)
            assert content is not None
            average_hash = bytes_to_hash(content)
            new_average_hashes[str(ord_id)] = average_hash
            save_new_avg_hash(str(ord_id), average_hash)
        except Exception as e:
            logger.exception(
                f"ERROR: could not get average hash of picture {ord_id} - {e}"
            )

    # merge average_hash_data with new_average_hashes and save it
    average_hash_data.update(new_average_hashes)
    save_new_data(average_hash_data)
    logger.info("Done!")


if __name__ == "__main__":
    main()
