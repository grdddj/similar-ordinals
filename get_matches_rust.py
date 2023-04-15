from __future__ import annotations

import ctypes
import json
from ctypes import c_char_p, c_int
from pathlib import Path
from typing import Optional

import typer

from common import Match, path_to_hash
from config import Config

# Load the shared Rust library
rust_lib = ctypes.cdll.LoadLibrary(str(Config.RUST_LIB_PATH))

# Define the return type and argument types for the Rust function
rust_lib.get_matches_c.argtypes = [c_char_p, c_char_p, c_char_p, c_int]
rust_lib.get_matches_c.restype = c_char_p


# Call the Rust function
def get_matches_rust(json_file: str, ord_id: str, file_hash: str, top_n: int) -> str:
    return rust_lib.get_matches_c(
        json_file.encode(), ord_id.encode(), file_hash.encode(), top_n
    ).decode()


def get_matches(
    json_file: str | Path, ord_id: str | None, file_hash: str | None, top_n: int
) -> list[Match]:
    rust_matches = get_matches_rust(
        str(json_file), ord_id or "", file_hash or "", top_n
    )
    return json.loads(rust_matches)


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
