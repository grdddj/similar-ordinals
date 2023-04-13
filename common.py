from __future__ import annotations

import io
from pathlib import Path
from typing import TypedDict

import numpy as np
from PIL import Image  # type: ignore

try:
    ANTIALIAS = Image.Resampling.LANCZOS
except AttributeError:
    # deprecated in pillow 10
    # https://pillow.readthedocs.io/en/stable/deprecations.html
    ANTIALIAS = Image.ANTIALIAS

HERE = Path(__file__).parent

img_folder = HERE / "images"
image_paths = [str(path) for path in img_folder.glob("*.jpg")]

hash_size = 16
db_file = HERE / f"average_hash_db_{hash_size}.json"


class Match(TypedDict):
    ord_id: str
    match_sum: int


def path_to_hash(image_path: str | Path) -> str:
    img = Image.open(image_path)
    return average_hash(img, hash_size)


def bytes_to_hash(data: bytes) -> str:
    img_file = io.BytesIO(data)
    img = Image.open(img_file)
    return average_hash(img, hash_size)


def average_hash(img: Image.Image, hash_size: int) -> str:
    """Creates a fingerprint of an image using the average hash algorithm.

    Actually copy-pasted code from imagehash.average_hash, so we do
    not need to bring in the whole library with scipy etc.

    Docs about the approach:
    https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html
    """
    # reduce size and complexity, then covert to grayscale
    img = img.convert("L").resize((hash_size, hash_size), ANTIALIAS)

    # find average pixel value; 'pixels' is an array of the pixel values, ranging from 0 (black) to 255 (white)
    pixels = np.asarray(img)
    avg = np.mean(pixels)

    bool_array = pixels > avg
    int_array = bool_array.flatten().astype(int)
    binary_string = "".join(map(str, int_array))
    return binary_string
