from __future__ import annotations

import ctypes
import json
from ctypes import c_char_p, c_int
from pathlib import Path

import click

from common import Match, db_file, image_to_hash_bin_str

# Load the shared Rust library
rust_lib = ctypes.cdll.LoadLibrary(
    "similar_pictures/target/release/libsimilar_pictures.so"
)

# Define the return type and argument types for the Rust function
rust_lib.get_matches_c.argtypes = [c_char_p, c_char_p, c_char_p, c_int]
rust_lib.get_matches_c.restype = c_char_p


# Call the Rust function
def get_matches_rust(json_file: str, ord_id: str, file_hash: str, top_n: int) -> str:
    return rust_lib.get_matches_c(
        json_file.encode(), ord_id.encode(), file_hash.encode(), top_n
    ).decode()


def get_matches(
    json_file: str | Path, ord_id: str, file_hash: str, top_n: int
) -> list[Match]:
    rust_matches = get_matches_rust(str(json_file), ord_id, file_hash, top_n)
    return json.loads(rust_matches)


@click.command()
@click.option("-j", "--json-file", type=click.Path(exists=True), default=db_file)
@click.option("-c", "--custom-file", type=click.Path(exists=True), default=None)
@click.option("-o", "--ord-id", default="")
@click.option("-f", "--file-hash", default="")
@click.option("-n", "--top-n", type=int, default=20)
def main(
    json_file: Path,
    custom_file: Path,
    ord_id: str,
    file_hash: str,
    top_n: int,
) -> None:
    if custom_file is not None:
        file_hash = image_to_hash_bin_str(custom_file)
    matches = get_matches(json_file, ord_id, file_hash, top_n)
    for match in matches:
        print(match)


if __name__ == "__main__":
    main()
