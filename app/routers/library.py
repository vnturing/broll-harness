from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from ..database import get_db, VideoRecord
from ..models.video import LibraryVideo, TagUpdateRequest

router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("", response_model=List[LibraryVideo])
async def list_library(db: Session = Depends(get_db)):
    records = db.query(VideoRecord).order_by(VideoRecord.created_at.desc()).all()
    return records


@router.delete("/{video_id}")
async def delete_video(video_id: str, db: Session = Depends(get_db)):
    record = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")

    if record.filepath:
        p = Path(record.filepath)
        if p.exists():
            p.unlink()

    db.delete(record)
    db.commit()
    return {"deleted": video_id}


@router.patch("/{video_id}/tags")
async def update_tags(
    video_id: str,
    body: TagUpdateRequest,
    db: Session = Depends(get_db),
):
    record = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    record.tags = body.tags
    db.commit()
    return {"id": video_id, "tags": record.tags}


@router.get("/file/{video_id}")
async def serve_file(video_id: str, db: Session = Depends(get_db)):
    record = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
    if not record or not record.filepath:
        raise HTTPException(status_code=404, detail="File not found")
    p = Path(record.filepath)
    if not p.exists():
        raise HTTPException(status_code=404, detail="File missing from disk")
    return FileResponse(str(p), media_type="video/mp4", filename=p.name)
