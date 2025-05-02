from fastapi import FastAPI
import app.models
from .db.init_db import init_db
from .api.auth import router as auth_router

from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import contextmanager

app = FastAPI(debug=True)


@contextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8090, reload=True)
