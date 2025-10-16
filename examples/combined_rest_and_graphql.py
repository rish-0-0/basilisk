"""
Combined REST and GraphQL example for Basilisk.

This example demonstrates using BOTH REST and GraphQL APIs together
in the same FastAPI application. Developers can use whichever API
style they prefer, or even both!

To run this example:
    1. Install basilisk with dev dependencies: pip install -e ".[dev]"
    2. Run the server: python examples/combined_rest_and_graphql.py
    3. Try both APIs!

REST API:
    - Swagger docs: http://localhost:8000/docs
    - List users: http://localhost:8000/api/users/
    - Documentation: http://localhost:8000/api/users/documentation

GraphQL API:
    - GraphQL Playground: http://localhost:8000/graphql/
    - View schema: http://localhost:8000/schema
"""

from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel, Field
from basilisk import CRUDRouter, GraphQLCRUDRouter

# ============================================================================
# Database Setup
# ============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./example_combined.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # Set to True to see SQL queries
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

    name: str = Field(..., min_length=1, max_length=100)
    email: str
    age: int | None = Field(None, ge=0, le=150)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    name: str | None = Field(None, min_length=1, max_length=100)
    email: str | None = None
    age: int | None = Field(None, ge=0, le=150)


class UserResponse(BaseModel):
    """Schema for user responses."""

    id: int
    name: str
    email: str
    age: int | None = None

    model_config = {"from_attributes": True}


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Basilisk Combined Example",
    description="Using both REST and GraphQL APIs together",
    version="0.1.0",
)

# Create database tables
Base.metadata.create_all(bind=engine)


# ============================================================================
# REST API Router
# ============================================================================

rest_router = CRUDRouter(
    model=User,
    create_schema=UserCreate,
    response_schema=UserResponse,
    get_db=get_db,
    prefix="/api/users",
    tags=["REST API - Users"],
)

app.include_router(rest_router.router)


# ============================================================================
# GraphQL Router
# ============================================================================

graphql_router = GraphQLCRUDRouter(
    model=User,
    create_schema=UserCreate,
    update_schema=UserUpdate,
    response_schema=UserResponse,
    get_db=get_db,
    path="/graphql",
    resource_name="User",
)

app.mount("/graphql", graphql_router.app)


# ============================================================================
# Additional Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
def read_root():
    """Welcome endpoint with API information."""
    return {
        "message": "Welcome to Basilisk Combined Example!",
        "description": "This app provides BOTH REST and GraphQL APIs",
        "apis": {
            "rest": {
                "base_url": "/api/users/",
                "swagger_docs": "/docs",
                "documentation": "/api/users/documentation",
                "examples": {
                    "list": "GET /api/users/",
                    "get": "GET /api/users/{id} (coming soon)",
                    "create": "POST /api/users/ (coming soon)",
                }
            },
            "graphql": {
                "endpoint": "/graphql/",
                "playground": "Visit /graphql/ in browser",
                "schema": "/schema",
                "examples": {
                    "list": "query { users { id name email } }",
                    "create": "mutation { createUser(input: {...}) { id name } }",
                }
            }
        },
        "tip": "Choose the API style that fits your needs - or use both!"
    }


@app.get("/schema", tags=["GraphQL"])
def get_schema():
    """Get the GraphQL schema."""
    return {"schema": graphql_router.schema_str}


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
    print("🦎 Basilisk Combined REST + GraphQL Example")
    print("="*70)
    print("\n📡 REST API:")
    print("   • Swagger Docs: http://localhost:8000/docs")
    print("   • List users: http://localhost:8000/api/users/")
    print("   • Documentation: http://localhost:8000/api/users/documentation")
    print("\n🎮 GraphQL API:")
    print("   • Playground: http://localhost:8000/graphql/")
    print("   • Schema: http://localhost:8000/schema")
    print("\n🏠 Home: http://localhost:8000/")
    print("\n💡 Tip: Same data, two APIs - use whichever you prefer!\n")
    print("="*70 + "\n")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
