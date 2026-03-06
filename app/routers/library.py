from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path

from ..database import get_db, VideoRecord, Project
from ..models.video import LibraryVideo, TagUpdateRequest, ProjectAssignRequest

router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("", response_model=List[LibraryVideo])
async def list_library(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(VideoRecord)
    if project_id is not None:
        q = q.filter(VideoRecord.project_id == project_id)
    return q.order_by(VideoRecord.created_at.desc()).all()


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


@router.patch("/{video_id}/project")
async def assign_project(
    video_id: str,
    body: ProjectAssignRequest,
    db: Session = Depends(get_db),
):
    record = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")

    if body.project_id:
        project = db.query(Project).filter(Project.id == body.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Move the file to the project directory if it exists
        if record.filepath:
            src = Path(record.filepath)
            if src.exists():
                dest = Path(project.directory) / src.name
                src.rename(dest)
                record.filepath = str(dest)

    record.project_id = body.project_id
    db.commit()
    return {"id": video_id, "project_id": record.project_id}


@router.get("/file/{video_id}")
async def serve_file(video_id: str, db: Session = Depends(get_db)):
    record = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
    if not record or not record.filepath:
        raise HTTPException(status_code=404, detail="File not found")
    p = Path(record.filepath)
    if not p.exists():
        raise HTTPException(status_code=404, detail="File missing from disk")
    return FileResponse(str(p), media_type="video/mp4", filename=p.name)
