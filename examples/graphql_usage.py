"""
GraphQL usage example for Basilisk.

This example demonstrates how to create GraphQL CRUD operations using Basilisk.
You can use GraphQL alongside REST, or use GraphQL exclusively.

To run this example:
    1. Install basilisk with GraphQL support: pip install -e ".[dev]"
    2. Run the server: python examples/graphql_usage.py
    3. Open GraphQL playground at http://localhost:8000/graphql
    4. Try running queries and mutations!

Example GraphQL queries to try:

# Query all users
query {
  users(skip: 0, limit: 10) {
    id
    name
    email
    age
  }
}

# Get single user
query {
  user(id: 1) {
    id
    name
    email
  }
}

# Create a user
mutation {
  createUser(input: {
    name: "John Doe"
    email: "john@example.com"
    age: 30
  }) {
    id
    name
    email
  }
}

# Update a user
mutation {
  updateUser(id: 1, input: {
    name: "Jane Doe"
  }) {
    id
    name
    email
  }
}

# Delete a user
mutation {
  deleteUser(id: 1)
}
"""

from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel, Field
from basilisk import GraphQLCRUDRouter

# ============================================================================
# Database Setup
# ============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./example_graphql_users.db"

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


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    name: str | None = Field(None, min_length=1, max_length=100, description="User's full name")
    email: str | None = Field(None, description="User's email address")
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
    title="Basilisk GraphQL Example",
    description="Example of using Basilisk to generate GraphQL CRUD operations",
    version="0.1.0",
)

# Create database tables
Base.metadata.create_all(bind=engine)


# ============================================================================
# Generate GraphQL Router with Basilisk
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

# Mount the GraphQL app
app.mount("/graphql", graphql_router.app)


# ============================================================================
# Additional Endpoints (Optional)
# ============================================================================

@app.get("/", tags=["Root"])
def read_root():
    """Welcome endpoint."""
    return {
        "message": "Welcome to Basilisk GraphQL Example!",
        "graphql_endpoint": "/graphql",
        "graphql_playground": "Visit /graphql in your browser to open GraphQL Playground",
        "tip": "Try the example queries from the docstring at the top of this file!",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "basilisk-graphql-example"}


@app.get("/schema", tags=["Schema"])
def get_schema():
    """Get the generated GraphQL schema."""
    return {
        "schema": graphql_router.schema_str,
        "description": "This is the auto-generated GraphQL schema from your Pydantic models"
    }


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
    print("🦎 Basilisk GraphQL Example Server")
    print("="*70)
    print(f"\n🎮 GraphQL Playground: http://localhost:8000/graphql")
    print(f"📜 GraphQL Schema: http://localhost:8000/schema")
    print(f"🏠 Home: http://localhost:8000/")
    print(f"\n💡 Tip: Visit /graphql to use the interactive GraphQL playground!\n")
    print("="*70 + "\n")

    print("Example GraphQL queries to try:")
    print("-" * 70)
    print("""
# List all users
query {
  users {
    id
    name
    email
  }
}

# Create a user
mutation {
  createUser(input: {
    name: "Alice"
    email: "alice@example.com"
    age: 25
  }) {
    id
    name
  }
}
""")
    print("="*70 + "\n")

    uvicorn.run(
        app,
        host="127.0.0.1",  # Use localhost for better Windows compatibility
        port=8000,
        log_level="info",
    )
