from fastapi import FastAPI
from .db.init_db import init_db
from .api.user import router as users
from .api.auth import router as auth_router

from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import contextmanager

app = FastAPI(debug=True)


@contextmanager
def lifespan(app: FastAPI):
    init_db()
    yield


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users, prefix="/api")
app.include_router(auth_router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8090, reload=True)
