# B-Roll Harness

A local research workbench for finding, previewing, and archiving royalty-free video clips.  
Search Pexels, Pixabay, Internet Archive, and YouTube from one interface. Downloads land in `./downloads/`.

---

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — fast Python package manager
- `ffmpeg` — for video processing
  ```bash
  brew install ffmpeg          # macOS
  # apt install ffmpeg         # Debian/Ubuntu
  ```
- `yt-dlp` — install once via uv or system package manager
  ```bash
  uv tool install yt-dlp
  ```

### Local (no Docker)

```bash
# Clone and enter the project
git clone <repo-url>
cd broll-harness

# 1. Install dependencies
make dev          # installs all deps (including dev tools)
# or: make install  (production deps only)

# 2. Copy and fill in API keys
cp .env.example .env

# 3. Run the dev server
make run
```

Open http://localhost:8000

### Manual uv commands

```bash
uv sync                        # install all deps
uv sync --no-dev               # production only
uv run uvicorn app.main:app --reload --port 8000
uv run pytest                  # run tests
```

---

### Docker

```bash
cd docker
PEXELS_API_KEY=xxx PIXABAY_API_KEY=yyy docker-compose up --build
```

---

## Makefile Targets

| Target       | Description                              |
|--------------|------------------------------------------|
| `make install` | Install production dependencies only   |
| `make dev`   | Install all dependencies (incl. dev)     |
| `make run`   | Start the uvicorn dev server             |
| `make test`  | Run tests with pytest                    |
| `make format`| Format code with ruff                   |
| `make lint`  | Lint code with ruff                     |
| `make clean` | Remove `.venv` and cache directories     |

---

## API Keys

| Source           | Where to get                              | Free tier          |
|------------------|-------------------------------------------|--------------------|
| Pexels           | https://www.pexels.com/api/               | Unlimited, free    |
| Pixabay          | https://pixabay.com/api/docs/             | Unlimited, free    |
| Internet Archive | No key needed                             | —                  |
| YouTube          | yt-dlp handles this locally               | —                  |

---

## API Reference

```
GET  /api/search?q={query}&sources={csv}   Search across sources
POST /api/download                          Queue a download
GET  /api/download/status/{id}             Poll download status
GET  /api/library                          List all downloads
DELETE /api/library/{id}                   Remove a clip + file
PATCH  /api/library/{id}/tags             Update clip tags
GET  /api/library/file/{id}               Stream the local file
```

---

## Architecture

```
Browser (Alpine.js)
    │
    ▼
FastAPI (thin control layer)
    ├── /api/search  ──→  Pexels API
    │                ──→  Pixabay API
    │                ──→  Archive.org API
    │                ──→  yt-dlp (YouTube metadata)
    │
    ├── /api/download ──→  BackgroundTask
    │                       ├── yt-dlp (YouTube)
    │                       └── httpx stream (others)
    │
    └── /api/library ──→  SQLite (library.db)
```

---

## Project Structure

```
broll-harness/
├── app/
│   ├── main.py              FastAPI app
│   ├── config.py            Env vars & paths
│   ├── database.py          SQLAlchemy + SQLite
│   ├── routers/
│   │   ├── search.py        GET /api/search
│   │   ├── download.py      POST /api/download
│   │   └── library.py       GET/DELETE /api/library
│   ├── services/
│   │   ├── pexels_service.py
│   │   ├── pixabay_service.py
│   │   ├── archive_service.py
│   │   ├── youtube_service.py
│   │   └── download_service.py
│   ├── models/video.py      Pydantic schemas
│   └── templates/index.html Single-page UI
├── downloads/               Local clip archive
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── pyproject.toml           Project metadata & deps (uv)
├── uv.lock                  Lockfile (committed to git)
├── Makefile                 Common dev shortcuts
└── README.md
```

---

## Extending

To add a new source (e.g. Coverr, Mixkit):

1. Create `app/services/coverr_service.py`
2. Implement `async def search_coverr(query, n) -> List[VideoResult]`
3. Import and call it in `app/routers/search.py`
4. Add its toggle to the `sources` array in `index.html`

That's it. The UI handles the rest.

---

## License

MIT. Do your own due diligence on the licenses of clips you download.  
- Pexels: CC0  
- Pixabay: Pixabay License (free commercial use)  
- Internet Archive: Public Domain / varies  
- YouTube: check each video individually
