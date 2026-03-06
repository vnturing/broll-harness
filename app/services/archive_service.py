import httpx
from typing import List
from ..models.video import VideoResult

ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_BASE = "https://archive.org"


async def search_archive(query: str, rows: int = 10) -> List[VideoResult]:
    params = {
        "q": f"{query} AND mediatype:movies",
        "fl[]": ["identifier", "title", "description", "subject", "runtime"],
        "rows": rows,
        "output": "json",
        "sort[]": "downloads desc",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(ARCHIVE_SEARCH, params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        docs = data.get("response", {}).get("docs", [])

        for doc in docs:
            identifier = doc.get("identifier", "")
            title = doc.get("title", "Untitled")
            runtime = doc.get("runtime")

            # Parse runtime string like "00:01:23" to seconds
            duration = None
            if runtime and isinstance(runtime, str):
                parts = runtime.split(":")
                try:
                    if len(parts) == 3:
                        duration = (
                            int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        )
                    elif len(parts) == 2:
                        duration = int(parts[0]) * 60 + int(parts[1])
                except ValueError:
                    pass

            thumbnail = f"{ARCHIVE_BASE}/services/img/{identifier}"
            preview_url = f"{ARCHIVE_BASE}/embed/{identifier}"
            download_url = f"{ARCHIVE_BASE}/download/{identifier}"

            results.append(
                VideoResult(
                    id=f"archive_{identifier}",
                    title=title,
                    source="archive",
                    duration=duration,
                    thumbnail=thumbnail,
                    preview_url=preview_url,
                    download_url=download_url,
                    license="Public Domain / Various Open Licenses",
                )
            )

        return results

    except Exception as e:
        print(f"[Archive] Error: {e}")
        return []
