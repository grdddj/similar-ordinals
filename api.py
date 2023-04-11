# Deployed by:
# uvicorn api:app --reload --host 0.0.0.0 --port 8000
from __future__ import annotations

from fastapi import FastAPI, Query, UploadFile

from common import bytes_to_hash, db_file
from get_matches_rust import get_matches

app = FastAPI()

# curl http://localhost:8000/ord_id/123?top_n=10
@app.get("/ord_id/{ord_id}")
async def by_ord_id(ord_id: int, top_n: int = Query(20)):
    matches = get_matches(db_file, str(ord_id), "", top_n)
    return {"matches": matches}


# curl -X POST -H "Content-Type: multipart/form-data" -F "file=@images/1.jpg" http://localhost:8000/file?top_n=10
@app.post("/file")
async def by_custom_file(file: UploadFile, top_n: int = Query(20)):
    file_bytes = await file.read()
    file_hash = bytes_to_hash(file_bytes)
    matches = get_matches(db_file, "", file_hash, top_n)
    return {"matches": matches}
