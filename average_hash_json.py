from __future__ import annotations

import json

import imagehash
from PIL import Image

from common import db_file, hash_size, image_paths


def image_to_hash_bin_str(image_path: str) -> str:
    with Image.open(image_path) as img:
        bool_array = imagehash.average_hash(img, hash_size).hash
        int_array = bool_array.flatten().astype(int)
        binary_string = "".join(map(str, int_array))
        return binary_string


def save_average_hashes(files: list[str]) -> None:
    avg_hashes: dict[str, str] = {}
    for img_path in files:
        img_hash_bin_string = image_to_hash_bin_str(img_path)
        file_name = img_path.split("/")[-1]
        print("file_name", file_name)
        avg_hashes[file_name] = img_hash_bin_string

    with open(db_file, "w") as f:
        json.dump(avg_hashes, f, indent=4)


if __name__ == "__main__":
    save_average_hashes(image_paths)
