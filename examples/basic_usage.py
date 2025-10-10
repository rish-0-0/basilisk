"""
Basic usage example for Basilisk.

This example demonstrates the simplest way to create CRUD routes for a User model.

To run this example:
    1. Install basilisk with dev dependencies: pip install -e ".[dev]"
    2. Run the server: python examples/basic_usage.py
    3. Open your browser to http://localhost:8000/docs
    4. Try out the API endpoints!

Available endpoints:
    - GET    /users/           - List all users (with pagination)
    - GET    /users/{id}       - Get a specific user (not yet implemented)
    - POST   /users/           - Create a new user (not yet implemented)
    - PUT    /users/{id}       - Update a user (not yet implemented)
    - DELETE /users/{id}       - Delete a user (not yet implemented)
    - GET    /users/documentation - Swagger docs for User endpoints
"""

from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel, Field
from basilisk import CRUDRouter

# ============================================================================
# Database Setup
# ============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./example_users.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True,  # Set to False to disable SQL logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Database dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# SQLAlchemy Model
# ============================================================================

class User(Base):
    """User model - represents a user in the database."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class UserCreate(BaseModel):
    """Schema for creating a new user."""

    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")
    age: int | None = Field(None, ge=0, le=150, description="User's age")


class UserResponse(BaseModel):
    """Schema for user responses."""

    id: int = Field(..., description="Unique user ID")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    age: int | None = Field(None, description="User's age")

    model_config = {"from_attributes": True}


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Basilisk Basic Example",
    description="A simple example of using Basilisk to generate CRUD routes",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Create database tables
Base.metadata.create_all(bind=engine)


# ============================================================================
# Generate CRUD Router with Basilisk
# ============================================================================

user_router = CRUDRouter(
    model=User,
    create_schema=UserCreate,
    response_schema=UserResponse,
    get_db=get_db,
    prefix="/users",
    tags=["Users"],
)

# Include the router in the app
app.include_router(user_router.router)


# ============================================================================
# Additional Custom Endpoints (Optional)
# ============================================================================

@app.get("/", tags=["Root"])
def read_root():
    """Welcome endpoint."""
    return {
        "message": "Welcome to Basilisk Basic Example!",
        "documentation": "Visit /docs for interactive API documentation",
        "endpoints": {
            "users_list": "/users/",
            "users_docs": "/users/documentation (coming soon)",
            "swagger": "/docs",
            "redoc": "/redoc",
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "basilisk-example"}


# ============================================================================
# Run the Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    import sys

    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("\n" + "="*70)
    print("🦎 Basilisk Basic Example Server")
    print("="*70)
    print(f"\n📚 Interactive API Docs: http://localhost:8000/docs")
    print(f"📖 ReDoc Documentation: http://localhost:8000/redoc")
    print(f"👥 Users API: http://localhost:8000/users/")
    print(f"\n💡 Tip: Visit /docs to try out the API interactively!\n")
    print("="*70 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
