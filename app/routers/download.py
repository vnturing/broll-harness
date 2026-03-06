from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, VideoRecord, Project
from ..models.video import DownloadRequest, LibraryVideo
from ..services.download_service import run_download

router = APIRouter(prefix="/api/download", tags=["download"])


@router.post("", response_model=LibraryVideo)
async def start_download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Validate project if provided
    if request.project_id:
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    # Check if already downloaded
    existing = db.query(VideoRecord).filter(VideoRecord.id == request.id).first()
    if existing and existing.status == "complete":
        return existing

    # Create or reset record
    if not existing:
        record = VideoRecord(
            id=request.id,
            title=request.title,
            source=request.source,
            thumbnail=request.thumbnail,
            original_url=request.download_url,
            duration=request.duration,
            project_id=request.project_id,
            status="pending",
        )
        db.add(record)
    else:
        existing.status = "pending"
        if request.project_id:
            existing.project_id = request.project_id
        record = existing

    db.commit()
    db.refresh(record)

    background_tasks.add_task(run_download, request, db)

    return record


@router.get("/status/{video_id}")
async def get_status(video_id: str, db: Session = Depends(get_db)):
    record = db.query(VideoRecord).filter(VideoRecord.id == video_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Download not found")
    return {"id": record.id, "status": record.status, "filepath": record.filepath}
