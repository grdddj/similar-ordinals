from __future__ import annotations

import heapq
from pathlib import Path
from typing import Iterator, Optional

import orjson  # quicker in parsing the file than json
import typer

from common import Match, path_to_hash
from config import Config

HERE = Path(__file__).parent


def get_matches(
    json_file: str | Path, ord_id: str | None, file_hash: str | None, top_n: int = 20
) -> list[Match]:
    with open(json_file) as f:
        data = orjson.loads(f.read())["data"]

    int_data = {k: int(v, 2) for k, v in data.items()}
    return get_matches_from_int_data(int_data, ord_id, file_hash, top_n)


def get_matches_from_int_data(
    data: dict[str, int], ord_id: str | None, file_hash: str | None, top_n: int = 20
) -> list[Match]:
    if ord_id:
        if ord_id not in data:
            return []
        file_hash_int = data[ord_id]
    else:
        assert file_hash is not None
        file_hash_int = int(file_hash, 2)

    hash_length = Config.HASH_SIZE**2

    def match_generator() -> Iterator[tuple[str, int]]:
        for file_name, hash_int in data.items():
            # Comparing the string hashes by converting them to integers
            # and counting the number of different bits
            different_bit_int = file_hash_int ^ hash_int
            different_bit_count = bin(different_bit_int).count("1")
            same_bit_count = hash_length - different_bit_count
            # Also accounting for inverse matches - e.g. 11111111 and 00000000
            match_sum = max(same_bit_count, different_bit_count)
            yield file_name, match_sum

    best_matches = heapq.nlargest(top_n, match_generator(), key=lambda x: x[1])

    return [
        {"ord_id": ord_id, "match_sum": match_sum} for ord_id, match_sum in best_matches
    ]


def get_matches_from_data(
    data: dict[str, str], ord_id: str | None, file_hash: str | None, top_n: int = 20
) -> list[Match]:
    if ord_id:
        if ord_id not in data:
            return []
        file_hash = data[ord_id]
    assert file_hash is not None

    hash_length = len(file_hash)
    file_hash_int = int(file_hash, 2)

    def match_generator() -> Iterator[tuple[str, int]]:
        for file_name, hash in data.items():
            # Comparing the string hashes by converting them to integers
            # and counting the number of different bits
            hash_int = int(hash, 2)
            different_bit_int = file_hash_int ^ hash_int
            different_bit_count = bin(different_bit_int).count("1")
            same_bit_count = hash_length - different_bit_count
            # Also accounting for inversed matches - e.g. 11111111 and 00000000
            match_sum = max(same_bit_count, different_bit_count)
            yield file_name, match_sum

    best_matches = heapq.nlargest(top_n, match_generator(), key=lambda x: x[1])

    return [
        {"ord_id": ord_id, "match_sum": match_sum} for ord_id, match_sum in best_matches
    ]


def main(
    json_file: Path = typer.Option(
        Config.AVERAGE_HASH_DB, "-j", "--json-file", exists=True, help="JSON DB file"
    ),
    custom_file: Optional[Path] = typer.Option(
        None, "-c", "--custom-file", exists=True, help="Custom file"
    ),
    ord_id: Optional[str] = typer.Option(None, "-o", "--ord-id", help="Ordinal ID"),
    file_hash: Optional[str] = typer.Option(
        None, "-f", "--file-hash", help="Hash of the file"
    ),
    top_n: int = typer.Option(20, "-n", "--top-n", help="Number of matches to return"),
) -> None:
    if custom_file is not None:
        file_hash = path_to_hash(custom_file)
    matches = get_matches(json_file, ord_id, file_hash, top_n)
    for match in matches:
        print(match)


if __name__ == "__main__":
    typer.run(main)
