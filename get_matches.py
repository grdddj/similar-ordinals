from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from common import Match, db_file, path_to_hash

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


def main(
    json_file: Path = typer.Option(
        db_file, "-j", "--json-file", exists=True, help="JSON DB file"
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
