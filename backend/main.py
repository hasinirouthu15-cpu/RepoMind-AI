
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from model import ask_model
from skill import analyze_question
from tools import list_python_files

app = FastAPI(
    title="RepoMind AI",
    description="AI-powered codebase intelligence platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to RepoMind AI!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


class AskRequest(BaseModel):
    question: str


class ScanRequest(BaseModel):
    folder_path: str


@app.post("/ask")
def ask_ai(request: AskRequest):
    try:
        prompt = analyze_question(request.question)

        if prompt == "Please enter a question.":
            return {"error": prompt}

        answer = ask_model(prompt)

        return {
            "question": request.question,
            "answer": answer,
        }

    except Exception as error:
        return {
            "error": "AI request failed. Check whether Ollama is running.",
            "details": str(error),
        }


@app.post("/scan")
def scan_project(request: ScanRequest):
    try:
        files = list_python_files(request.folder_path)

        return {
            "folder": request.folder_path,
            "total_python_files": len(files),
            "files": files,
        }

    except Exception as error:
        return {
            "error": "Could not scan the project folder.",
            "details": str(error),
        }
