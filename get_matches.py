from __future__ import annotations

import json
from pathlib import Path

import click

from common import Match, db_file, image_to_hash_bin_str

HERE = Path(__file__).parent


def get_matches(
    json_file: str | Path, ord_id: str | None, file_hash: str | None, top_n: int = 20
) -> list[Match]:
    with open(json_file) as f:
        data = json.load(f)

    if ord_id is not None:
        file_hash = data[ord_id]
    assert file_hash is not None

    matches: list[tuple[str, int]] = []
    for file_name, hash in data.items():
        match_sum = sum(c1 == c2 for c1, c2 in zip(file_hash, hash))
        matches.append((file_name, match_sum))

    matches.sort(key=lambda x: x[1], reverse=True)
    best_matches = matches[:top_n]
    return [
        {"ord_id": ord_id, "match_sum": match_sum} for ord_id, match_sum in best_matches
    ]


@click.command()
@click.option("-j", "--json-file", type=click.Path(exists=True), default=db_file)
@click.option("-c", "--custom-file", type=click.Path(exists=True), default=None)
@click.option("-o", "--ord-id", default=None)
@click.option("-f", "--file-hash", default=None)
@click.option("-n", "--top-n", type=int, default=20)
def main(
    json_file: Path,
    custom_file: Path,
    ord_id: str | None,
    file_hash: str | None,
    top_n: int,
) -> None:
    if custom_file is not None:
        file_hash = image_to_hash_bin_str(custom_file)
        print("file_hash", file_hash)
    matches = get_matches(json_file, ord_id, file_hash, top_n)
    for match in matches:
        print(match)


if __name__ == "__main__":
    main()
