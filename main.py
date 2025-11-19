import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import Clip

app = FastAPI(title="Anime Clips API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Anime Clips API is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# -------------------- Anime Clips Endpoints --------------------

class ClipCreate(BaseModel):
    title: str
    anime: str
    episode: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    notes: Optional[str] = None


@app.post("/api/clips")
def create_clip(payload: ClipCreate):
    try:
        # Validate using schema
        clip = Clip(**payload.model_dump())
        clip_id = create_document("clip", clip)
        return {"id": clip_id, "message": "Clip saved"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/clips")
def list_clips(limit: int = 50):
    try:
        items = get_documents("clip", {}, limit=limit)
        # Convert ObjectId to strings where needed
        for it in items:
            if "_id" in it:
                it["id"] = str(it.pop("_id"))
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
