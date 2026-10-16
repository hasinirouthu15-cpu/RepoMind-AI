
import logging
import os
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from model import ask_model
from skill import analyze_question
from tools import list_python_files

logger = logging.getLogger(__name__)
FRONTEND_INDEX = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
SCAN_ROOT = Path(os.environ["SCAN_ROOT"]).resolve() if os.environ.get("SCAN_ROOT") else None
ASK_RATE_LIMIT = 10
ASK_RATE_WINDOW_SECONDS = 60
ask_requests: dict[str, list[float]] = {}
ask_requests_lock = threading.Lock()

app = FastAPI(
    title="RepoMind AI",
    description="AI-powered codebase intelligence platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def limit_ai_requests(request: Request, call_next):
    if request.url.path == "/ask" and request.method == "POST":
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()

        with ask_requests_lock:
            if len(ask_requests) > 10_000:
                expired_before = now - ASK_RATE_WINDOW_SECONDS
                for ip, requests in list(ask_requests.items()):
                    active_requests = [timestamp for timestamp in requests if timestamp > expired_before]
                    if active_requests:
                        ask_requests[ip] = active_requests
                    else:
                        del ask_requests[ip]

            recent_requests = [
                timestamp
                for timestamp in ask_requests.get(client_ip, [])
                if timestamp > now - ASK_RATE_WINDOW_SECONDS
            ]
            if len(recent_requests) >= ASK_RATE_LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many AI requests. Please try again shortly."},
                )

            recent_requests.append(now)
            ask_requests[client_ip] = recent_requests

    return await call_next(request)


@app.get("/")
def home():
    return FileResponse(FRONTEND_INDEX)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


class AskRequest(BaseModel):
    question: str = Field(max_length=4000)


class ScanRequest(BaseModel):
    folder_path: str


@app.post("/ask")
def ask_ai(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Please enter a question.")

    try:
        prompt = analyze_question(request.question)
        answer = ask_model(prompt)

        return {
            "question": request.question,
            "answer": answer,
        }
    except Exception as error:
        logger.exception("AI request failed")
        raise HTTPException(
            status_code=502,
            detail="AI request failed. Check whether the Ollama service is available.",
        ) from error


@app.post("/scan")
def scan_project(request: ScanRequest):
    if SCAN_ROOT is None:
        raise HTTPException(status_code=503, detail="Project scanning is disabled on this server.")

    try:
        folder_path = Path(request.folder_path).resolve(strict=True)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="The requested folder was not found.") from error
    except (OSError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail="The requested folder path is invalid.") from error

    try:
        folder_path.relative_to(SCAN_ROOT)
    except ValueError as error:
        raise HTTPException(status_code=403, detail="The requested folder is outside the allowed scan directory.") from error

    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail="The requested path is not a directory.")

    try:
        files = list_python_files(str(folder_path))

        return {
            "folder": str(folder_path),
            "total_python_files": len(files),
            "files": files,
        }
    except Exception as error:
        logger.exception("Project scan failed")
        raise HTTPException(
            status_code=500,
            detail="Could not scan the project folder.",
        ) from error
