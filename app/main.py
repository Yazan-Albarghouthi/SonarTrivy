import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.database import init_db
from app.notes_service import (
    calculate_note_score,
    calculate_ratio,
    create_note,
    delete_note,
    get_note_by_id,
    list_notes,
    search_notes,
)
from app.security import generate_reset_token, is_admin, safe_calculator

init_db()

app = FastAPI(
    title="SonarTrivy Notes API",
    description="A secure notes API.",
    version="0.2.0",
)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


class NoteInput(BaseModel):
    title: str
    content: str
    owner: str
    is_private: bool = False


class LoginInput(BaseModel):
    username: str
    password: str


class CalculatorInput(BaseModel):
    expression: str


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "sonarTrivy"}


@app.post("/notes")
def add_note(note: NoteInput):
    try:
        created_note = create_note(
            title=note.title,
            content=note.content,
            owner=note.owner,
            is_private=note.is_private,
        )
        return created_note
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/notes")
def get_notes(
    keyword: Optional[str] = Query(default=None),
    owner: Optional[str] = Query(default=None),
):
    if keyword is not None:
        return search_notes(keyword=keyword, owner=owner)
    return list_notes()


@app.get("/notes/{note_id}")
def get_note(note_id: int):
    note = get_note_by_id(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.delete("/notes/{note_id}")
def remove_note(note_id: int):
    deleted = delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"deleted": True}


@app.post("/login")
def login(payload: LoginInput):
    if is_admin(payload.username, payload.password):
        return {"authenticated": True, "token": generate_reset_token()}
    return {"authenticated": False}


@app.post("/calculate")
def calculate(payload: CalculatorInput):
    try:
        result = safe_calculator(payload.expression)
    except (ValueError, ZeroDivisionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"result": result}


@app.get("/ratio")
def ratio(total: float, count: float):
    try:
        result = calculate_ratio(total, count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ratio": result}


@app.get("/notes/{note_id}/score")
def note_score(note_id: int):
    note = get_note_by_id(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    score = calculate_note_score(
        title=note["title"],
        content=note["content"],
        owner=note["owner"],
        is_private=bool(note["is_private"]),
        priority="high",
        has_attachment=False,
    )
    return {"note_id": note_id, "score": score}
