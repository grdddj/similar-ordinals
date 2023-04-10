from __future__ import annotations

import ctypes
import json
import threading
import time
from ctypes import c_char_p
from typing import TypedDict


class Match(TypedDict):
    ord_id: str
    match_sum: int


# Load the shared library
lib = ctypes.cdll.LoadLibrary("similar_pictures/target/release/libsimilar_pictures.so")

# Define the return type and argument types for the Rust function
lib.get_matches_c.argtypes = [c_char_p, c_char_p, c_char_p]
lib.get_matches_c.restype = c_char_p


# Call the Rust function
def get_matches_rust(json_file: str, ord_id: str, file_hash: str) -> str:
    return lib.get_matches_c(
        json_file.encode(), ord_id.encode(), file_hash.encode()
    ).decode()


def get_matches(json_file: str, ord_id: str, file_hash: str) -> list[Match]:
    rust_matches = get_matches_rust(json_file, ord_id, file_hash)
    return json.loads(rust_matches)


def save_match(ord_id: str, matches: list[Match]) -> None:
    with open("matches.txt", "a") as f:
        f.write(f"{ord_id}: {matches}\n")


if __name__ == "__main__":
    json_file = "average_hash_db_16.json"
    ord_id = "6666"
    file_hash = "0000000000000000000000000001110000000000001111100111010000111110011111110111111001111111000011100000000000001100000000000000100000000000000000000111111111111110001100010000000000000000000011100001111110010000001110111110000000111111111000000000000000000000"

    # matches = get_matches(json_file, ord_id, file_hash)
    # print(matches)

    # for ord_id, file_hash in db.items():
    #     print("ord_id", ord_id)
    #     matches = get_matches(json_file, ord_id, file_hash)
    #     print(matches)
    #     save_match(ord_id, matches)

    with open(json_file) as f:
        db = json.load(f)

    items = iter(db.items())

    def analyze():
        while True:
            try:
                item = next(items)
                ord_id, file_hash = item
                matches = get_matches(json_file, ord_id, file_hash)
                print(ord_id)
                save_match(ord_id, matches)
            except StopIteration:
                break

    no_of_threads = 4
    for _ in range(no_of_threads):
        new_thread = threading.Thread(target=analyze)
        new_thread.start()
        time.sleep(0.5)
