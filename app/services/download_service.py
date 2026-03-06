import asyncio
import httpx
import re
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from ..database import VideoRecord, Project
from ..models.video import DownloadRequest
from ..config import DOWNLOADS_DIR


def _safe_filename(title: str) -> str:
    safe = re.sub(r"[^\w\s-]", "", title).strip()
    safe = re.sub(r"[\s]+", "_", safe)
    return safe[:80] or "video"


async def _download_direct(url: str, dest: Path) -> bool:
    try:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with open(dest, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        f.write(chunk)
        return True
    except Exception as e:
        print(f"[Download] Direct download failed: {e}")
        return False


async def _download_ytdlp(url: str, dest_dir: Path, record_id: str) -> Path | None:
    output_template = str(dest_dir / f"{record_id}.%(ext)s")
    import shutil

    yt_dlp_path = shutil.which("yt-dlp") or "/root/.local/bin/yt-dlp"

    cmd = [
        yt_dlp_path,
        url,
        "-o",
        output_template,
        "--no-playlist",
        "--quiet",
        "--merge-output-format",
        "mp4",
        "-f",
        "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        if proc.returncode != 0:
            print(f"[yt-dlp] Error: {stderr.decode()}")
            return None

        # Find the downloaded file
        matches = list(dest_dir.glob(f"{record_id}.*"))
        return matches[0] if matches else None
    except asyncio.TimeoutError:
        print("[yt-dlp] Download timed out")
        return None
    except FileNotFoundError:
        print("[yt-dlp] Not installed")
        return None


async def run_download(request: DownloadRequest, db: Session):
    record = db.query(VideoRecord).filter(VideoRecord.id == request.id).first()
    if not record:
        return

    record.status = "downloading"
    db.commit()

    # Resolve destination directory
    dest_dir = DOWNLOADS_DIR
    if request.project_id:
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if project:
            dest_dir = Path(project.directory)
            dest_dir.mkdir(parents=True, exist_ok=True)

    try:
        safe_name = _safe_filename(request.title)
        filepath = None

        if request.source == "youtube":
            # Use yt-dlp for YouTube
            result_path = await _download_ytdlp(
                request.download_url, dest_dir, request.id.replace("/", "_")
            )
            if result_path:
                filepath = str(result_path)
        else:
            # Direct HTTP download for Pexels, Pixabay, Archive
            ext = "mp4"
            url = request.download_url
            if "archive.org/download/" in url:
                url = await _resolve_archive_url(url)
            dest = dest_dir / f"{request.id}_{safe_name}.{ext}"
            success = await _download_direct(url, dest)
            if success:
                filepath = str(dest)

        if filepath:
            record.status = "complete"
            record.filepath = filepath
        else:
            record.status = "error"

    except Exception as e:
        print(f"[Download] Unhandled error: {e}")
        record.status = "error"

    db.commit()


async def _resolve_archive_url(base_url: str) -> str:
    """Attempt to find the best mp4 file from an Archive.org item."""
    # base_url is like https://archive.org/download/{identifier}
    try:
        identifier = base_url.rstrip("/").split("/")[-1]
        meta_url = f"https://archive.org/metadata/{identifier}"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(meta_url)
            data = response.json()
        files = data.get("files", [])
        mp4_files = [f for f in files if f.get("name", "").endswith(".mp4")]
        if mp4_files:
            best = sorted(mp4_files, key=lambda f: int(f.get("size", 0)), reverse=True)[
                0
            ]
            return f"https://archive.org/download/{identifier}/{best['name']}"
    except Exception as e:
        print(f"[Archive resolve] {e}")
    return base_url
