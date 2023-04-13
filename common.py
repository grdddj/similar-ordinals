from __future__ import annotations

import io
from pathlib import Path
from typing import TypedDict

import imagehash
from PIL import Image  # type: ignore

HERE = Path(__file__).parent

img_folder = HERE / "images"
image_paths = [str(path) for path in img_folder.glob("*.jpg")]

hash_size = 16
db_file = HERE / f"average_hash_db_{hash_size}.json"


class Match(TypedDict):
    ord_id: str
    match_sum: int


def path_to_hash(image_path: str | Path) -> str:
    with Image.open(image_path) as img:
        return image_to_hash(img)


def bytes_to_hash(data: bytes) -> str:
    img_file = io.BytesIO(data)
    image = Image.open(img_file)
    return image_to_hash(image)


def image_to_hash(img: Image.Image) -> str:
    bool_array = imagehash.average_hash(img, hash_size).hash
    int_array = bool_array.flatten().astype(int)
    binary_string = "".join(map(str, int_array))
    return binary_string
