from __future__ import annotations

import json
from pathlib import Path

from common import bytes_to_hash, get_logger
from config import Config
from db_files import get_data
from db_ord_data import get_all_image_inscriptions_iter

HERE = Path(__file__).parent

log_file_path = HERE / "avg_hash.log"
logger = get_logger(__file__, log_file_path)


def main() -> None:
    avg_hashes: dict[int, str] = {}
    try:
        index = 0
        for incsr in get_all_image_inscriptions_iter():
            index += 1
            if index % 100 == 0:
                logger.info(f"index {index}")

            try:
                data = get_data(incsr.tx_id)  # type: ignore
                if data is not None:
                    avg_hashes[incsr.id] = bytes_to_hash(data)
            except Exception as e:
                logger.error(f"ERROR: {incsr} - {e}")
                continue
    except KeyboardInterrupt:
        pass
    finally:
        with open(Config.AVERAGE_HASH_DB, "w") as f:
            results = {"data": avg_hashes}
            json.dump(results, f, indent=1)


if __name__ == "__main__":
    main()
