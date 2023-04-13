# Deployed by:
# uvicorn api:app --reload --host 0.0.0.0 --port 8001
from __future__ import annotations

import json

from fastapi import FastAPI, Query, UploadFile

from common import Match, bytes_to_hash, db_file
from db_ord_data import InscriptionModel
from db_similarity_index import SimilarityIndex
from get_matches import get_matches_from_data

app = FastAPI()

USE_ORD_ID_INDEX = True

# Loading the data globally, so it is immediately available for all requests
with open(db_file) as f:
    data = json.load(f)


def get_full_inscription_result(match: Match) -> dict:
    inscription = InscriptionModel.by_id(int(match["ord_id"]))
    inscr_dict = inscription.dict()
    inscr_dict["similarity"] = match["match_sum"]
    inscr_dict["ordinals_com_link"] = inscription.ordinals_com_link()
    inscr_dict["ordinals_com_content_link"] = inscription.ordinals_com_content_link()
    inscr_dict["hiro_content_link"] = inscription.hiro_content_link()
    inscr_dict[
        "ordinalswallet_content_link"
    ] = inscription.ordinalswallet_content_link()
    inscr_dict["mempool_space_link"] = inscription.mempool_space_link()
    return inscr_dict


# curl http://localhost:8001/ord_id/123?top_n=10
@app.get("/ord_id/{ord_id}")
async def by_ord_id(ord_id: int, top_n: int = Query(20)):
    if USE_ORD_ID_INDEX:
        matches: list[Match] = [
            {"ord_id": str(match_ord_id), "match_sum": match_sum}
            for match_ord_id, match_sum in SimilarityIndex.list_by_id(ord_id)[:top_n]
        ]
    else:
        matches = get_matches_from_data(data, str(ord_id), None, top_n)
    result = [get_full_inscription_result(match) for match in matches]
    return {"result": result}


# curl -X POST -H "Content-Type: multipart/form-data" -F "file=@images/1.jpg" http://localhost:8001/file?top_n=10
@app.post("/file")
async def by_custom_file(file: UploadFile, top_n: int = Query(20)):
    file_bytes = await file.read()
    file_hash = bytes_to_hash(file_bytes)
    matches = get_matches_from_data(data, None, file_hash, top_n)
    result = [get_full_inscription_result(match) for match in matches]
    return {"result": result}
