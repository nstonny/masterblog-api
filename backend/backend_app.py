"""
Development (with auto-reload):
uvicorn backend.backend_app:app --host 0.0.0.0 --port 5002 --reload
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

app = FastAPI(title="Masterblog API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    empty_fields = []

    for error in exc.errors():
        field_name = error['loc'][-1]
        if error['type'] == 'string_too_short':
            empty_fields.append(field_name)

    if empty_fields:
        return JSONResponse(
            status_code=422,
            content={"error": f"Empty fields: {', '.join(empty_fields)}"}
        )

    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request data", "details": exc.errors()}
    )


#------------Using pydantic models for built-in validation--------------
class PostCreate(BaseModel):
    title: str = Field(min_length=1, description="Title cannot be empty")
    content: str = Field(min_length=1, description="Content cannot be empty")


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class Post(BaseModel):
    id: int
    title: str
    content: str

POSTS: list[dict] = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]

def _next_id():
    return max((p['id'] for p in POSTS), default=0) + 1


#------------Routes--------------------------------
@app.get("/api/posts")
def get_posts():
    return POSTS

@app.post("/api/posts", response_model=Post, status_code=201)
def add_post(post: PostCreate):
    new_post = {"id": _next_id(), "title": post.title, "content": post.content}
    POSTS.append(new_post)
    return new_post


