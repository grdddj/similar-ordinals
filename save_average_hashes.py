from __future__ import annotations

import json

from common import db_file, image_paths, path_to_hash


def save_average_hashes(files: list[str]) -> None:
    avg_hashes: dict[str, str] = {}
    for img_path in files:
        img_hash_bin_string = path_to_hash(img_path)
        file_name = img_path.split("/")[-1]
        print("file_name", file_name)
        avg_hashes[file_name] = img_hash_bin_string

    with open(db_file, "w") as f:
        json.dump(avg_hashes, f, indent=4)


if __name__ == "__main__":
    save_average_hashes(image_paths)
