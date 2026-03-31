from fastapi import FastAPI

from src.routes import auth
from src.routes import post
from src.routes import feed
from src.routes import like
from src.core.logging import logger

app = FastAPI()

app.include_router(auth.router)
app.include_router(post.router)
app.include_router(feed.router)
app.include_router(like.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
