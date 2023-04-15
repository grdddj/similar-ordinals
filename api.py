# Deployed by:
# uvicorn api:app --reload --host 0.0.0.0 --port 8001
from __future__ import annotations

import json
import logging
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from common import Match, bytes_to_hash
from config import Config
from db_ord_data import InscriptionModel
from db_similarity_index import SimilarityIndex
from get_matches import get_matches_from_data
from rust_server import get_matches_from_rust_server

HERE = Path(__file__).parent

log_file_path = HERE / "server.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)

app = FastAPI()

# This is the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USE_ORD_ID_INDEX = True


# Storing the data globally, so it is immediately available for all requests
# Not loading it right away, as Rust server should be handling this
# Loading them as soon as the Rust server fails and we need to fallback into Python
average_hash_data: dict[str, str] = {}


def load_average_hash_data_if_not_there() -> None:
    global average_hash_data

    if not average_hash_data:
        logging.info("Loading the average_hash_data from JSON")
        with open(Config.AVERAGE_HASH_DB) as f:
            average_hash_data = json.load(f)["data"]
        logging.info("Finished loading average_hash_data")


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


def get_client_ip(request: Request) -> str:
    if request.client is None:
        return "ghost"
    return request.client.host


def generate_random_id():
    return secrets.token_hex(5)


# curl http://localhost:8001/ord_id/123?top_n=10
@app.get("/ord_id/{ord_id}")
async def by_ord_id(request: Request, ord_id: int, top_n: int = Query(20)):
    try:
        request_id = generate_random_id()
        logging.info(
            f"req_id: {request_id}, HOST: {get_client_ip(request)}, ord_id: {ord_id}, top_n: {top_n}"
        )
        result = do_by_ord_id(ord_id, top_n)
        logging.info(f"req_id: {request_id}: request finished")
        return {"result": result}
    except Exception as e:
        logging.exception(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def do_by_ord_id(ord_id: int, top_n: int = 20) -> list[dict]:
    # Index is the fastest way to get the results - just then try Rust
    if USE_ORD_ID_INDEX and SimilarityIndex.is_defined(ord_id):
        matches: list[Match] = [
            {"ord_id": str(match_ord_id), "match_sum": match_sum}
            for match_ord_id, match_sum in SimilarityIndex.list_by_id(ord_id)[:top_n]
        ]
    else:
        try:
            matches = get_matches_from_rust_server(ord_id, None)
        except Exception as e:
            logging.error(f"Error from Rust server: {e}")
            load_average_hash_data_if_not_there()
            matches = get_matches_from_data(average_hash_data, str(ord_id), None, top_n)
    # We must make sure that the requested ord_id is in the results
    # (it may not be, when there is a lot of duplicates)
    if matches and ord_id not in [int(match["ord_id"]) for match in matches]:
        matches.pop()
        matches.append({"ord_id": str(ord_id), "match_sum": 256})
    return [get_full_inscription_result(match) for match in matches[:top_n]]


# curl -X POST -H "Content-Type: multipart/form-data" -F "file=@images/1.jpg" http://localhost:8001/file?top_n=10
@app.post("/file")
async def by_custom_file(request: Request, file: UploadFile, top_n: int = Query(20)):
    try:
        request_id = generate_random_id()
        logging.info(
            f"req_id: {request_id}, HOST: {get_client_ip(request)}, filename: {file.filename}, size: {file.size}, top_n: {top_n}"
        )
        file_bytes = await file.read()
        result = do_by_custom_file(file_bytes, top_n)
        logging.info(f"req_id: {request_id}: request finished")
        return {"result": result}
    except Exception as e:
        logging.exception(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def do_by_custom_file(file_bytes: bytes, top_n: int = 20) -> list[dict]:
    file_hash = bytes_to_hash(file_bytes)
    try:
        matches = get_matches_from_rust_server(None, file_hash)
    except Exception as e:
        logging.error(f"Error from Rust server: {e}")
        load_average_hash_data_if_not_there()
        matches = get_matches_from_data(average_hash_data, None, file_hash, top_n)
    return [get_full_inscription_result(match) for match in matches[:top_n]]


# curl http://localhost:8001/
@app.get("/")
async def get_docs(request: Request):
    try:
        request_id = generate_random_id()
        logging.info(f"DOCS - req_id: {request_id}, HOST: {get_client_ip(request)}")
        return {
            "docs": "Go to https://github.com/grdddj/similar-ordinals#api to see the API docs and supported endpoints",
            "example": "Get 10 most similar ordinals to the ordinal with ID 0: https://api.ordsimilarity.com/ord_id/0?top_n=10",
        }
    except Exception as e:
        logging.exception(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
