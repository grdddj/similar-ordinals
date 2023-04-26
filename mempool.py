from __future__ import annotations

import requests

possible_image_formats = ["png", "webp", "jpeg", "svg", "gif"]
base_url = "https://ordmempool.space/static/pictures/"


def get_link_and_content_from_mempool(tx_id: str) -> tuple[str | None, bytes | None]:
    for image_format in possible_image_formats:
        url = base_url + tx_id + "." + image_format
        response = requests.get(url)
        if response.status_code == 200:
            return url, response.content
    return None, None
