import asyncio
import json
from typing import List
from ..models.video import VideoResult
from ..config import YTDLP_SEARCH_COUNT


async def search_youtube(query: str, count: int = None) -> List[VideoResult]:
    n = count or YTDLP_SEARCH_COUNT
    search_term = f"ytsearch{n}:{query}"

    import shutil

    yt_dlp_path = shutil.which("yt-dlp") or "/root/.local/bin/yt-dlp"

    cmd = [
        yt_dlp_path,
        search_term,
        "--dump-json",
        "--no-playlist",
        "--quiet",
        "--no-warnings",
        "--skip-download",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        print("[YouTube] yt-dlp timed out")
        return []
    except FileNotFoundError:
        print("[YouTube] yt-dlp not found — install it with: pip install yt-dlp")
        return []
    except Exception as e:
        print(f"[YouTube] Subprocess error: {e}")
        return []

    results = []
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            info = json.loads(line)
        except json.JSONDecodeError:
            continue

        video_id = info.get("id", "")
        title = info.get("title", "Untitled")
        duration = info.get("duration")
        thumbnail = info.get("thumbnail")
        webpage_url = info.get(
            "webpage_url", f"https://www.youtube.com/watch?v={video_id}"
        )

        # Prefer a mid-quality thumbnail
        thumbnails = info.get("thumbnails", [])
        if thumbnails:
            mid = thumbnails[len(thumbnails) // 2]
            thumbnail = mid.get("url", thumbnail)

        results.append(
            VideoResult(
                id=f"youtube_{video_id}",
                title=title,
                source="youtube",
                duration=duration,
                thumbnail=thumbnail,
                preview_url=f"https://www.youtube.com/embed/{video_id}",
                download_url=webpage_url,
                license="YouTube (check individual video license)",
            )
        )

    return results
