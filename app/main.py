from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from .database import init_db
from .routers import search, download, library, projects

app = FastAPI(title="B-Roll Harness", version="1.0.0")


# Init DB on startup
@app.on_event("startup")
async def startup():
    init_db()


# Static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Routers
app.include_router(search.router)
app.include_router(download.router)
app.include_router(library.router)
app.include_router(projects.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
