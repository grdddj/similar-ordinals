from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import imagehash
from PIL import Image

HERE = Path(__file__).parent

img_folder = HERE / "images"
image_paths = [str(path) for path in img_folder.glob("*.jpg")]

hash_size = 16
db_file = HERE / f"average_hash_db_{hash_size}.json"


class Match(TypedDict):
    ord_id: str
    match_sum: int


def image_to_hash_bin_str(image_path: str | Path) -> str:
    with Image.open(image_path) as img:
        bool_array = imagehash.average_hash(img, hash_size).hash
        int_array = bool_array.flatten().astype(int)
        binary_string = "".join(map(str, int_array))
        return binary_string
