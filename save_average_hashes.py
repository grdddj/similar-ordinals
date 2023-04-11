from __future__ import annotations

import json
import logging
from pathlib import Path

import imagehash
from db_data import get_all_image_inscriptions_iter
from PIL import Image

from common import bytes_to_hash
from db_files import get_data

HERE = Path(__file__).parent

log_file_path = HERE / "avg_hash.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)

hash_size = 16
db_file = f"average_hash_db_{hash_size}.json"


def image_to_hash_bin_str(img: Image.Image) -> str:
    bool_array = imagehash.average_hash(img, hash_size).hash
    int_array = bool_array.flatten().astype(int)
    binary_string = "".join(map(str, int_array))
    return binary_string


if __name__ == "__main__":
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
            json.dump(avg_hashes, f, indent=4)
