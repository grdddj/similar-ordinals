from __future__ import annotations

import requests  # type: ignore

from common import Match


def get_matches_from_rust_server(
    ord_id: int | None, file_hash: str | None
) -> list[Match]:
    url = "http://localhost:8081"
    if ord_id is not None:
        endpoint = f"/ord_id/{ord_id}"
    elif file_hash is not None:
        endpoint = f"/file_hash/{file_hash}"
    else:
        raise ValueError("ord_id and file_hash are both None")

    response = requests.get(url + endpoint, timeout=2)
    response.raise_for_status()
    return response.json()
