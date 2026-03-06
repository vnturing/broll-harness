import httpx
from typing import List
from ..models.video import VideoResult
from ..config import PIXABAY_API_KEY


async def search_pixabay(query: str, per_page: int = 10) -> List[VideoResult]:
    if not PIXABAY_API_KEY:
        return []

    url = "https://pixabay.com/api/videos/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": query,
        "per_page": per_page,
        "video_type": "film",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        for video in data.get("hits", []):
            videos = video.get("videos", {})
            # Prefer large > medium > small > tiny
            best = (
                videos.get("large")
                or videos.get("medium")
                or videos.get("small")
                or videos.get("tiny")
                or {}
            )

            results.append(
                VideoResult(
                    id=f"pixabay_{video['id']}",
                    title=f"{query.title()} — Pixabay #{video['id']}",
                    source="pixabay",
                    duration=video.get("duration"),
                    thumbnail=video.get("userImageURL") or video.get("picture_id"),
                    preview_url=best.get("url"),
                    download_url=best.get("url"),
                    license="Pixabay License (Free for commercial use)",
                    width=best.get("width"),
                    height=best.get("height"),
                )
            )
        return results

    except Exception as e:
        print(f"[Pixabay] Error: {e}")
        return []
