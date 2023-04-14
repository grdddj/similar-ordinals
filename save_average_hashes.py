from __future__ import annotations

import json
import logging
from pathlib import Path

from common import bytes_to_hash, db_file
from db_files import get_data
from db_ord_data import get_all_image_inscriptions_iter

HERE = Path(__file__).parent

log_file_path = HERE / "avg_hash.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)


def main() -> None:
    avg_hashes: dict[int, str] = {}
    try:
        index = 0
        for incsr in get_all_image_inscriptions_iter():
            index += 1
            if index % 100 == 0:
                logging.info(f"index {index}")

            try:
                data = get_data(incsr.tx_id)  # type: ignore
                if data is not None:
                    avg_hashes[incsr.id] = bytes_to_hash(data)
            except Exception as e:
                logging.error(f"ERROR: {incsr} - {e}")
                continue
    except KeyboardInterrupt:
        pass
    finally:
        with open(db_file, "w") as f:
            results = {"data": avg_hashes}
            json.dump(results, f, indent=1)


if __name__ == "__main__":
    main()
