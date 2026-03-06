from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VideoResult(BaseModel):
    id: str
    title: str
    source: str  # pexels | pixabay | youtube | archive
    duration: Optional[float] = None
    thumbnail: Optional[str] = None
    preview_url: Optional[str] = None
    download_url: Optional[str] = None
    license: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    class Config:
        from_attributes = True


class DownloadRequest(BaseModel):
    id: str
    title: str
    source: str
    download_url: str
    thumbnail: Optional[str] = None
    duration: Optional[float] = None


class LibraryVideo(BaseModel):
    id: str
    title: str
    source: str
    filepath: Optional[str]
    duration: Optional[float]
    tags: Optional[str]
    thumbnail: Optional[str]
    original_url: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TagUpdateRequest(BaseModel):
    tags: str
