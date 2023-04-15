from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

import requests  # type: ignore

from common import bytes_to_hash, db_file
from db_files import ByteData
from db_files import get_session as get_files_session
from db_ord_data import InscriptionModel
from db_ord_data import get_session as get_data_session

HERE = Path(__file__).parent

log_file_path = HERE / "update_data.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)

new_hashes_file = HERE / "new_average_hashes.txt"

HIRO_API = "https://api.hiro.so/ordinals/v1/inscriptions"
HIRO_CONTENT_API_TEMPLATE = "https://api.hiro.so/ordinals/v1/inscriptions/{}/content"

new_average_hashes: dict[str, str] = {}


def get_current_data() -> dict[str, str]:
    with open(db_file) as f:
        return json.load(f)["data"]


def save_new_data(new_data: dict[str, str]) -> None:
    with open(db_file, "w") as f:
        results = {"data": new_data}
        json.dump(results, f, indent=1)


def get_our_last_id(data: dict[str, str]) -> int:
    return max(int(k) for k in data.keys())


def get_missing_amount(our_last_id: int) -> int:
    params = {"limit": 1, "from_number": our_last_id + 1}
    r = requests.get(HIRO_API, params=params)
    r.raise_for_status()
    data = r.json()

    total_missing = data["total"]
    return total_missing


def save_new_avg_hash(ord_id: str, avg_hash: str) -> None:
    with open(new_hashes_file, "a") as f:
        f.write(f"{ord_id} {avg_hash}\n")


def get_ord_id_content(ord_id: int) -> bytes:
    r = requests.get(HIRO_CONTENT_API_TEMPLATE.format(ord_id))
    r.raise_for_status()
    return r.content


def process_batch(limit: int, from_number: int, to_number: int) -> None:
    logging.info(f"Processing batch {from_number} - {to_number}")
    params = {"limit": limit, "from_number": from_number, "to_number": to_number}
    r = requests.get(HIRO_API, params=params)
    r.raise_for_status()
    data = r.json()

    files_db_session = get_files_session()
    ord_data_session = get_data_session()

    for entry in data["results"]:
        # if not entry["content_type"].startswith("image/"):
        #     continue

        # Get content from another endpoint
        ord_id: int = entry["number"]
        content_data = get_ord_id_content(ord_id)

        # Try to get average hashes for all the images
        content_type = entry["content_type"]
        if content_type.startswith("image/"):
            try:
                average_hash = bytes_to_hash(content_data)
                new_average_hashes[str(ord_id)] = average_hash
                save_new_avg_hash(str(ord_id), average_hash)
            except Exception as e:
                logging.exception(
                    f"ERROR: could not get average hash of picture {ord_id} - {entry} - {e}"
                )

        # Save content to db if not there already
        if files_db_session.query(ByteData).get(entry["tx_id"]) is None:
            byte_data = ByteData(id=entry["tx_id"], data=content_data)
            files_db_session.add(byte_data)

        # Save ord_data to db if not there already
        if ord_data_session.query(InscriptionModel).get(ord_id) is None:
            content_hash = hashlib.md5(content_data).hexdigest()
            timestamp_ms = entry["timestamp"]
            unix_timestamp = timestamp_ms // 1000
            str_datetime = datetime.fromtimestamp(unix_timestamp).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            inscr = InscriptionModel(
                id=ord_id,
                tx_id=entry["tx_id"],
                minted_address=entry["address"],
                content_type=content_type,
                content_hash=content_hash,
                datetime=str_datetime,
                timestamp=unix_timestamp,
                content_length=entry["content_length"],
                genesis_fee=int(entry["genesis_fee"]),
                genesis_height=entry["genesis_block_height"],
                output_value=int(entry["value"]),
            )
            ord_data_session.add(inscr)

    files_db_session.commit()
    ord_data_session.commit()


def main() -> None:
    average_hash_data = get_current_data()
    last_id = get_our_last_id(average_hash_data)
    logging.info(f"Last id: {last_id}")
    total_missing = get_missing_amount(last_id)
    logging.info(f"Total missing: {total_missing}")

    processed = 0
    while processed < total_missing:
        limit = 60
        from_number = last_id + 1 + processed
        to_number = from_number + limit - 1
        process_batch(limit, from_number, to_number)
        processed += limit

    # merge average_hash_data with new_average_hashes and save it
    average_hash_data.update(new_average_hashes)
    save_new_data(average_hash_data)
    logging.info("Done!")


if __name__ == "__main__":
    main()
