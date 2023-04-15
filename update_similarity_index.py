import json
import logging
from pathlib import Path

from common import db_file
from db_similarity_index import SimilarityIndex, get_highest_id
from get_matches import get_matches_from_data

HERE = Path(__file__).parent

log_file_path = HERE / "update_similarity_index.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)


highest_indexed_id = get_highest_id()
logging.info(f"highest_indexed_id {highest_indexed_id}")

with open(db_file, "r") as f:
    data = json.load(f)["data"]

already_indexed_data = {k: v for k, v in data.items() if int(k) <= highest_indexed_id}
not_indexed_data = {k: v for k, v in data.items() if int(k) > highest_indexed_id}

# calculate the index for all the ord_ids higher than highest_indexed_id
for progress, (ord_id, average_hash) in enumerate(not_indexed_data.items()):
    if progress % 100 == 0:
        logging.info(f"New update progress {progress} / {len(not_indexed_data)}")
    matches = get_matches_from_data(data, ord_id=None, file_hash=average_hash, top_n=20)
    list_of_lists = [[int(match["ord_id"]), match["match_sum"]] for match in matches]
    SimilarityIndex.save_new(ord_id, list_of_lists)


# calculate the similarities for older ones - but just with new ones
for progress, (old_ord_id, old_average_hash) in enumerate(already_indexed_data.items()):
    if progress % 1000 == 0:
        logging.info(f"Old update progress {progress} / {len(already_indexed_data)}")
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
    SimilarityIndex.update_old(int(old_ord_id), new_top_matches)
