# Deployed by:
# uvicorn api:app --reload --host 0.0.0.0 --port 8002
from __future__ import annotations

import json
import random
import secrets
from pathlib import Path
from typing import Union

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from common import Match, bytes_to_hash, content_md5_hash, get_logger
from config import Config
from db_ord_data import InscriptionModel
from db_similarity_index import SimilarityIndex
from get_matches import get_matches_from_data
from rust_server import get_matches_from_rust_server
from update_data import (
    create_inscription_model_from_api_data,
    get_ord_id_content,
    get_specific_ord_id,
)

HERE = Path(__file__).parent

log_file_path = HERE / "server.log"
logger = get_logger(__file__, log_file_path)

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
RANDOM_ORD_ID = "random"


# Storing the data globally, so it is immediately available for all requests
with open(Config.AVERAGE_HASH_DB) as f:
    average_hash_data: dict[str, str] = json.load(f)["data"]
highest_id_we_have = max(int(k) for k in average_hash_data.keys())
logger.info(
    f"We have {len(average_hash_data):_} entries - max is {highest_id_we_have:_}."
)


def get_full_inscription_result(match: Match) -> dict:
    inscription = InscriptionModel.by_id(int(match["ord_id"]))
    return get_result_with_having_inscription(match, inscription)


def get_result_with_having_inscription(
    match: Match, inscription: InscriptionModel
) -> dict:
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
async def by_ord_id(request: Request, ord_id: Union[int, str], top_n: int = Query(20)):
    try:
        request_id = generate_random_id()
        logger.info(
            f"req_id: {request_id}, HOST: {get_client_ip(request)}, ord_id: {ord_id}, top_n: {top_n}"
        )
        # Possibility to select a random one
        if ord_id == RANDOM_ORD_ID:
            ord_id = random.choice(list(average_hash_data.keys()))
        # Check we have a valid int ord_id
        try:
            ord_id = int(ord_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ord_id must be an integer")
        result = do_by_ord_id(ord_id, top_n)
        # get the content hash of chosen ordinal
        chosen_ord_content_hash = ""
        for match in result:
            if str(match.get("id")) == str(ord_id):
                chosen_ord_content_hash = match.get("content_hash", "")
        logger.info(f"req_id: {request_id}: request finished")
        return {
            "result": result,
            "ord_id": ord_id,
            "ord_content_hash": chosen_ord_content_hash,
        }
    except Exception as e:
        logger.exception(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def do_by_ord_id(ord_id: int, top_n: int = 20) -> list[dict]:
    # Index is the fastest way to get the results - just then try Rust
    if USE_ORD_ID_INDEX and SimilarityIndex.is_defined(ord_id):
        matches: list[Match] = [
            {"ord_id": str(match_ord_id), "match_sum": match_sum}
            for match_ord_id, match_sum in SimilarityIndex.list_by_id(ord_id)[:top_n]
        ]
    else:
        if ord_id not in average_hash_data:
            return do_by_ord_id_we_do_not_have(ord_id, top_n)
        else:
            try:
                matches = get_matches_from_rust_server(ord_id, None)
            except Exception as e:
                logger.error(f"Error from Rust server: {e}")
                matches = get_matches_from_data(
                    average_hash_data, str(ord_id), None, top_n
                )
    # We must make sure that the requested ord_id is in the results
    # (it may not be, when there is a lot of duplicates)
    if matches and ord_id not in [int(match["ord_id"]) for match in matches]:
        matches.pop()
        matches.append({"ord_id": str(ord_id), "match_sum": 256})
    return [get_full_inscription_result(match) for match in matches[:top_n]]


def do_by_ord_id_we_do_not_have(ord_id: int, top_n: int = 20) -> list[dict]:
    if ord_id < highest_id_we_have:
        logger.error(f"Not a valid picture - {ord_id}")
        return []
    else:
        # Downloading it in real time
        try:
            ord_data_bytes = get_ord_id_content(ord_id)
            ord_id_data = get_specific_ord_id(ord_id)
            inscription = create_inscription_model_from_api_data(
                ord_id_data, ord_data_bytes
            )
            results = do_by_custom_file(ord_data_bytes, top_n)
            # add the requested one to the results
            match: Match = {
                "ord_id": str(ord_id),
                "match_sum": 256,
            }
            new_result = get_result_with_having_inscription(match, inscription)
            results.append(new_result)
            return results
        except Exception as e:
            logger.error(f"Could not download/parse picture - {ord_id}, {e}")
            return []


# curl -X POST -H "Content-Type: multipart/form-data" -F "file=@images/1.jpg" http://localhost:8001/file?top_n=10
@app.post("/file")
async def by_custom_file(request: Request, file: UploadFile, top_n: int = Query(20)):
    try:
        request_id = generate_random_id()
        logger.info(
            f"req_id: {request_id}, HOST: {get_client_ip(request)}, filename: {file.filename}, size: {file.size}, top_n: {top_n}"
        )
        file_bytes = await file.read()
        result = do_by_custom_file(file_bytes, top_n)
        file_content_hash = content_md5_hash(file_bytes)
        logger.info(f"req_id: {request_id}: request finished")
        return {"result": result, "ord_content_hash": file_content_hash}
    except Exception as e:
        logger.exception(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def do_by_custom_file(file_bytes: bytes, top_n: int = 20) -> list[dict]:
    file_hash = bytes_to_hash(file_bytes)
    try:
        matches = get_matches_from_rust_server(None, file_hash)
    except Exception as e:
        logger.error(f"Error from Rust server: {e}")
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
        logger.exception(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
