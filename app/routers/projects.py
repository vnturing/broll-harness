import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path

from ..database import get_db, Project
from ..models.video import ProjectCreate, ProjectOut
from ..config import DOWNLOADS_DIR

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:60] or "project"


@router.get("", response_model=List[ProjectOut])
async def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    slug = _slugify(body.name)

    # Make slug unique
    base = slug
    counter = 1
    while db.query(Project).filter(Project.id == slug).first():
        slug = f"{base}-{counter}"
        counter += 1

    project_dir = DOWNLOADS_DIR / slug
    project_dir.mkdir(parents=True, exist_ok=True)

    project = Project(
        id=slug,
        name=body.name,
        description=body.description or "",
        directory=str(project_dir),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Unlink videos from project (keep them in library)
    for video in project.videos:
        video.project_id = None
    db.delete(project)
    db.commit()
    return {"deleted": project_id}
