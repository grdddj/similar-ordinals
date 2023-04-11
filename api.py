# Deployed by:
# uvicorn api:app --reload --host 0.0.0.0 --port 8001
from __future__ import annotations

from fastapi import FastAPI, Query, UploadFile

from common import Match, bytes_to_hash, db_file
from db_ord_data import InscriptionModel
from db_similarity_index import SimilarityIndex
from get_matches_rust import get_matches

app = FastAPI()

USE_INDEX = True


def matches_to_api_result(matches: list[Match]) -> list[dict]:
    result: list[dict] = []
    for match in matches:
        match_ord_id = match["ord_id"]
        # TODO: maybe send match_sum as well, to be shown in the UI?
        inscription = InscriptionModel.by_id(int(match_ord_id))
        result.append(inscription.dict())
    return result


# curl http://localhost:8001/ord_id/123?top_n=10
@app.get("/ord_id/{ord_id}")
async def by_ord_id(ord_id: int, top_n: int = Query(20)):
    if USE_INDEX:
        result: list[dict] = []
        for match_ord_id, _ in SimilarityIndex.list_by_id(ord_id)[:top_n]:
            inscription = InscriptionModel.by_id(int(match_ord_id))
            result.append(inscription.dict())
    else:
        matches = get_matches(db_file, str(ord_id), "", top_n)
        result = matches_to_api_result(matches)
    return {"result": result}


# curl -X POST -H "Content-Type: multipart/form-data" -F "file=@images/1.jpg" http://localhost:8001/file?top_n=10
@app.post("/file")
async def by_custom_file(file: UploadFile, top_n: int = Query(20)):
    file_bytes = await file.read()
    file_hash = bytes_to_hash(file_bytes)
    matches = get_matches(db_file, "", file_hash, top_n)
    result = matches_to_api_result(matches)
    return {"result": result}
