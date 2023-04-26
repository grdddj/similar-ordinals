from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import time

import requests  # type: ignore
from requests.exceptions import HTTPError

from common import bytes_to_hash, content_md5_hash, get_logger
from config import Config
from db_files import ByteData
from db_files import get_session as get_files_session
from db_ord_data import InscriptionModel
from db_ord_data import get_session as get_data_session

HERE = Path(__file__).parent

log_file_path = HERE / "update_data.log"
logger = get_logger(__file__, log_file_path)

new_hashes_file = HERE / "new_average_hashes.txt"

last_checked_file = HERE / "last_checked_id.dat"

try:
    last_checked_id = int(last_checked_file.read_text())
except Exception as e:
    logger.exception(f"Could not read last_checked_id from file - {e}")
    last_checked_id = None

HIRO_API = "https://api.hiro.so/ordinals/v1/inscriptions"
HIRO_CONTENT_API_TEMPLATE = "https://api.hiro.so/ordinals/v1/inscriptions/{}/content"

QUICK_PICTURE_UPDATE = True

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


def get_content_from_hiro_by_ord_id(ord_id: int) -> bytes | None:
    r = requests.get(HIRO_CONTENT_API_TEMPLATE.format(ord_id))
    if r.status_code == 200:
        return r.content
    return None


def get_hiro_content_link_from_ord_id(ord_id: int) -> str:
    return HIRO_CONTENT_API_TEMPLATE.format(ord_id)


def get_hiro_content_link_from_tx_id(tx_id: str) -> str | None:
    data = get_from_hiro_by_tx_id(tx_id)
    if not data:
        return None
    ord_id = data["number"]
    return get_hiro_content_link_from_ord_id(ord_id)


def get_from_hiro_by_ord_id(ord_id: int | str) -> dict:
    params = {"limit": 1, "from_number": ord_id, "to_number": ord_id}
    r = requests.get(HIRO_API, params=params)
    r.raise_for_status()
    data = r.json()
    return data["results"][0]


def get_from_hiro_by_tx_id(tx_id: str) -> dict | None:
    url = f"{HIRO_API}/{tx_id}i0"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None


def process_batch(limit: int, from_number: int, to_number: int) -> None:
    logger.info(f"Processing batch {from_number} - {to_number}")
    params = {"limit": limit, "from_number": from_number, "to_number": to_number}
    r = requests.get(HIRO_API, params=params)
    r.raise_for_status()
    data = r.json()

    if not QUICK_PICTURE_UPDATE:
        files_db_session = get_files_session()
    ord_data_session = get_data_session()

    for entry in data["results"]:
        if QUICK_PICTURE_UPDATE:
            if not entry["content_type"].startswith("image/"):
                continue

        # Get content from another endpoint
        ord_id: int = entry["number"]
        content_data = get_content_from_hiro_by_ord_id(ord_id)
        if not content_data:
            logger.error(f"Cant get content for {ord_id}")
            continue

        # Try to get average hashes for all the images
        content_type = entry["content_type"]
        if content_type.startswith("image/"):
            try:
                average_hash = bytes_to_hash(content_data)
                new_average_hashes[str(ord_id)] = average_hash
                save_new_avg_hash(str(ord_id), average_hash)
            except Exception as e:
                logger.error(
                    f"ERROR: could not get average hash of picture {ord_id} - {e}"
                )

        # Save content to db if not there already
        if not QUICK_PICTURE_UPDATE:
            if files_db_session.query(ByteData).get(entry["tx_id"]) is None:
                byte_data = ByteData(id=entry["tx_id"], data=content_data)
                files_db_session.add(byte_data)

        # Save ord_data to db if not there already
        if ord_data_session.query(InscriptionModel).get(ord_id) is None:
            try:
                inscr_model = create_inscription_model_from_api_data(entry, content_data)
                ord_data_session.add(inscr_model)
            except Exception as e:
                logger.error(f"ERROR: could not save ord_data {ord_id} - {e}")

    if not QUICK_PICTURE_UPDATE:
        files_db_session.commit()
    ord_data_session.commit()


def create_inscription_model_from_api_data(
    data: dict, content_data: bytes
) -> InscriptionModel:
    content_hash = content_md5_hash(content_data)
    timestamp_ms = data["timestamp"]
    unix_timestamp = timestamp_ms // 1000
    str_datetime = datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return InscriptionModel(
        id=data["number"],
        tx_id=data["tx_id"],
        minted_address=data["address"],
        content_type=data["content_type"],
        content_hash=content_hash,
        datetime=str_datetime,
        timestamp=unix_timestamp,
        content_length=data["content_length"],
        genesis_fee=int(data["genesis_fee"]),
        genesis_height=data["genesis_block_height"],
        output_value=int(data["value"]),
        sat_index=0,
    )


def main() -> None:
    average_hash_data = get_current_data()
    if last_checked_id is not None:
        last_id = last_checked_id
    else:
        last_id = get_our_last_id(average_hash_data)
    logger.info(f"Last id: {last_id}")
    logger.info(f"Initial average hashes count: {len(average_hash_data)}")
    total_missing = get_missing_amount(last_id)
    logger.info(f"Total missing: {total_missing}")

    processed = 0
    while processed < total_missing:
        try:
            limit = 60
            from_number = last_id + 1 + processed
            to_number = from_number + limit - 1
            process_batch(limit, from_number, to_number)
            processed += limit
        except HTTPError:
            logger.error("HTTPError, retrying")
            time.sleep(5)
            continue
        except Exception as e:
            logger.exception(f"ERROR: {e}")
            continue
    
    new_last_id = last_id + total_missing
    last_checked_file.write_text(str(new_last_id))

    # merge average_hash_data with new_average_hashes and save it
    average_hash_data.update(new_average_hashes)
    save_new_data(average_hash_data)
    logger.info(f"New average hashes count: {len(new_average_hashes)}")
    logger.info("Done!")


if __name__ == "__main__":
    main()
