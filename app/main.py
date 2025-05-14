from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from .db.connection import Database
from .api.auth import router as auth_router
from .api.customer import router as customer_router
from .api.staff import router as staff_router
from .api.admin import router as admin_router
import os

SERVER = os.environ.get("SERVER")
DATABASE = os.environ.get("DATABASE")
USERNAME = os.environ.get("USERNAME_")
PASSWORD = os.environ.get("PASSWORD")
DRIVER = os.environ.get("DRIVER")
PORT = int(os.environ.get("PORT"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI to manage startup and shutdown events.
    Initializes the database connection on startup and closes it on shutdown.
    Uses synchronous operations for database connection management.
    """
    # Startup: Initialize database connection synchronously
    # Store database instance in app.state for access in routes
    app.state.db = Database(SERVER, DATABASE, PORT, USERNAME, PASSWORD)
    app.state.db.set_driver(DRIVER)
    try:
        app.state.db.connect()  # Test connection on startup (synchronous)
        print(f"The current MySQL version is {app.state.db.get_version()}")
    except Exception as e:
        raise Exception(f"Failed to initialize database connection: {str(e)}")

    yield  # Application runs here

    # Shutdown: Close database connection synchronously
    if hasattr(app.state, 'db') and app.state.db:
        app.state.db.close()

# Create FastAPI app with debug mode and lifespan handler
app = FastAPI(debug=True, lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers (e.g., auth router)
app.include_router(auth_router, prefix="/api")
app.include_router(customer_router, prefix="/api")
app.include_router(staff_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
# Optional: Add a root endpoint for testing


@app.get("/")
def root():
    return {"message": "Welcome to the AutoCare API"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8090, reload=True)
