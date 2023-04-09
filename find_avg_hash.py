from __future__ import annotations

import json
import time
from pathlib import Path

from average_hash_json import db_file, image_to_hash_bin_str

HERE = Path(__file__).parent

with open(db_file) as f:
    data = json.load(f)

file_to_compare = str(HERE / "images" / "84.jpg")

file_hash = image_to_hash_bin_str(file_to_compare)
print("file_hash", file_hash)

# file_hash = file_hash[:64]

now = time.perf_counter()
matches: list[tuple[str, int]] = []
for file_name, hash in data.items():
    match_sum = sum(c1 == c2 for c1, c2 in zip(file_hash, hash))
    matches.append((file_name, match_sum))
diff = time.perf_counter() - now

matches.sort(key=lambda x: x[1], reverse=True)
for match in matches[:20]:
    print(match)
print(diff)
