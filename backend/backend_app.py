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
@app.get("/api/posts/search")
def search_posts(title: Optional[str] = None, content: Optional[str] = None):
    matched_posts = []
    for post in POSTS:
        if title and title.lower() in post["title"].lower():
            if post not in matched_posts:
                matched_posts.append(post)
        if content and content.lower() in post["content"].lower():
            if post not in matched_posts:
                matched_posts.append(post)
    return matched_posts

@app.get("/api/posts")
def get_posts(sort: Optional[str] = None, direction: Optional[str] = None):
    # Validate sort field
    if sort and sort not in ["title", "content"]:
        raise HTTPException(status_code=400, detail="Invalid sort field. Must be 'title' or 'content'")

    # Validate direction
    if direction and direction not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction. Must be 'asc' or 'desc'")

    # Return original order if no sorting requested
    if not sort:
        return POSTS

    # Sort posts
    reverse = direction == "desc"
    sorted_posts = sorted(POSTS, key=lambda post: post[sort].lower(), reverse=reverse)
    return sorted_posts

@app.post("/api/posts", response_model=Post, status_code=201)
def add_post(post: PostCreate):
    new_post = {"id": _next_id(), "title": post.title, "content": post.content}
    POSTS.append(new_post)
    return new_post

@app.delete("/api/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    global POSTS
    post_exists = any(post["id"] == post_id for post in POSTS)
    if not post_exists:
        raise HTTPException(status_code=404, detail="Post not found")
    POSTS = [post for post in POSTS if post["id"] != post_id]

@app.put("/api/posts/{post_id}", response_model=Post)
def update_post(post_id: int, post: PostUpdate):
    for existing_post in POSTS:
        if existing_post["id"] == post_id:
            if post.title is not None:
                existing_post["title"] = post.title
            if post.content is not None:
                existing_post["content"] = post.content
            return existing_post
    raise HTTPException(status_code=404, detail="Post not found")





