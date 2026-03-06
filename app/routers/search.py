import asyncio
from fastapi import APIRouter, Query
from typing import List
from ..models.video import VideoResult
from ..services import pexels_service, pixabay_service, archive_service, youtube_service

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=List[VideoResult])
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    sources: str = Query(
        "pexels,pixabay,archive,youtube", description="Comma-separated sources"
    ),
):
    source_list = [s.strip() for s in sources.split(",")]

    tasks = []
    labels = []

    if "pexels" in source_list:
        tasks.append(pexels_service.search_pexels(q, per_page=8))
        labels.append("pexels")
    if "pixabay" in source_list:
        tasks.append(pixabay_service.search_pixabay(q, per_page=8))
        labels.append("pixabay")
    if "archive" in source_list:
        tasks.append(archive_service.search_archive(q, rows=6))
        labels.append("archive")
    if "youtube" in source_list:
        tasks.append(youtube_service.search_youtube(q, count=8))
        labels.append("youtube")

    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    combined: List[VideoResult] = []
    for label, result in zip(labels, all_results):
        if isinstance(result, Exception):
            print(f"[Search] {label} failed: {result}")
            continue
        combined.extend(result)

    return combined
