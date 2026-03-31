from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import auth
from src.routes import post
from src.routes import feed
from src.routes import like
from src.routes import reply
from src.core.logging import logger

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(post.router)
app.include_router(feed.router)
app.include_router(like.router)
app.include_router(reply.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
