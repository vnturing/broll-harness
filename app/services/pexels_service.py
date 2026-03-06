import httpx
from typing import List
from ..models.video import VideoResult
from ..config import PEXELS_API_KEY


async def search_pexels(query: str, per_page: int = 10) -> List[VideoResult]:
    if not PEXELS_API_KEY:
        return []

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": per_page, "size": "medium"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        for video in data.get("videos", []):
            # Pick best quality video file
            files = sorted(
                video.get("video_files", []),
                key=lambda f: f.get("width", 0),
                reverse=True,
            )
            best = next(
                (f for f in files if f.get("width", 0) <= 1920),
                files[0] if files else None,
            )

            thumbnail = None
            pictures = video.get("video_pictures", [])
            if pictures:
                thumbnail = pictures[0].get("picture")

            results.append(
                VideoResult(
                    id=f"pexels_{video['id']}",
                    title=video.get("user", {}).get("name", "Untitled") + f" — {query}",
                    source="pexels",
                    duration=video.get("duration"),
                    thumbnail=thumbnail,
                    preview_url=best.get("link") if best else None,
                    download_url=best.get("link") if best else None,
                    license="Creative Commons Zero (CC0)",
                    width=best.get("width") if best else None,
                    height=best.get("height") if best else None,
                )
            )
        return results

    except Exception as e:
        print(f"[Pexels] Error: {e}")
        return []
