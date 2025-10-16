"""
Example demonstrating Role-Based Access Control (RBAC) with Basilisk.

This example shows how to:
1. Configure permissions for different roles
2. Integrate authentication with RBAC
3. Protect REST and GraphQL endpoints
4. Implement resource-level permissions

Requirements:
    pip install fastapi sqlalchemy pydantic ariadne uvicorn
"""

from typing import List
from fastapi import FastAPI, Depends, Request, HTTPException
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel

from basilisk import (
    CRUDRouter,
    GraphQLCRUDRouter,
    PermissionConfig,
    UserContext,
)

# Database setup
Base = declarative_base()
engine = create_engine("sqlite:///./rbac_example.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# SQLAlchemy Model
class Post(Base):
    """Blog post model."""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    author_id = Column(Integer, nullable=False)  # User ID of the author
    status = Column(String, default="draft")  # draft, published


# Pydantic Schemas
class PostCreate(BaseModel):
    """Schema for creating a post."""
    title: str
    content: str
    author_id: int
    status: str = "draft"


class PostUpdate(BaseModel):
    """Schema for updating a post."""
    title: str | None = None
    content: str | None = None
    status: str | None = None


class PostResponse(BaseModel):
    """Schema for post responses."""
    id: int
    title: str
    content: str
    author_id: int
    status: str

    class Config:
        from_attributes = True


# User model extending UserContext
class User(UserContext):
    """User model with roles."""
    username: str
    email: str


# Database dependency
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Mock authentication - In production, use JWT, OAuth2, etc.
MOCK_USERS = {
    "admin_token": User(id=1, username="admin", email="admin@example.com", roles=["admin"]),
    "editor_token": User(id=2, username="editor", email="editor@example.com", roles=["editor"]),
    "viewer_token": User(id=3, username="viewer", email="viewer@example.com", roles=["viewer"]),
    "author_token": User(id=4, username="author", email="author@example.com", roles=["author"]),
}


async def get_current_user(request: Request) -> User:
    """
    Get current user from request.

    In production, this would:
    1. Extract JWT token from Authorization header
    2. Validate and decode the token
    3. Load user from database
    4. Return user with roles

    For this example, we use a simple token-based mock system.
    """
    # Get token from header
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.replace("Bearer ", "")

    # Look up user by token (mock)
    user = MOCK_USERS.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user


# Resource-level permission: Users can only edit their own posts (unless they're admin)
def can_edit_own_post(user: UserContext, post: Post) -> bool:
    """
    Check if user can edit a post.

    Rules:
    - Admin can edit any post
    - Authors can edit their own posts
    """
    if "admin" in user.roles:
        return True
    if "author" in user.roles and user.id == post.author_id:
        return True
    return False


# Configure permissions
permissions = PermissionConfig(
    roles={
        # Admin can do everything
        "admin": ["create", "read", "update", "delete"],

        # Editors can read and update
        "editor": ["read", "update"],

        # Authors can create and read
        "author": ["create", "read"],

        # Viewers can only read
        "viewer": ["read"],
    },
    # Allow anonymous users to read
    allow_anonymous={"read"},
    # Add custom check for updates
    custom_checks={
        "update": can_edit_own_post,
    }
)


# Create FastAPI app
app = FastAPI(
    title="RBAC Example",
    description="Demonstrating Role-Based Access Control with Basilisk",
    version="1.0.0",
)


# Create tables
Base.metadata.create_all(bind=engine)


# Create REST router with RBAC
rest_router = CRUDRouter(
    model=Post,
    create_schema=PostCreate,
    update_schema=PostUpdate,
    response_schema=PostResponse,
    get_db=get_db,
    prefix="/posts",
    tags=["Posts (REST)"],
    permissions=permissions,
    get_current_user=get_current_user,
)

app.include_router(rest_router.router)


# Create GraphQL router with RBAC
graphql_router = GraphQLCRUDRouter(
    model=Post,
    create_schema=PostCreate,
    update_schema=PostUpdate,
    response_schema=PostResponse,
    get_db=get_db,
    resource_name="Post",
    permissions=permissions,
    get_current_user=get_current_user,
)

app.mount("/graphql", graphql_router.app)


# Public endpoint (no authentication required)
@app.get("/")
def read_root():
    """Public endpoint."""
    return {
        "message": "Welcome to RBAC Example",
        "endpoints": {
            "rest": "/posts",
            "graphql": "/graphql",
            "docs": "/docs",
        },
        "authentication": {
            "method": "Bearer token",
            "available_tokens": {
                "admin": "admin_token - Full access (create, read, update, delete)",
                "editor": "editor_token - Read and update access",
                "author": "author_token - Create and read access",
                "viewer": "viewer_token - Read-only access",
            },
            "example": "curl -H 'Authorization: Bearer admin_token' http://localhost:8000/posts",
        },
        "testing": {
            "rest": {
                "list": "GET /posts (no auth required for read)",
                "create": "POST /posts (requires: author or admin)",
                "update": "PUT /posts/{id} (requires: editor or admin, or author if own post)",
                "delete": "DELETE /posts/{id} (requires: admin only)",
            },
            "graphql": {
                "endpoint": "/graphql",
                "query_example": """
                    query {
                        posts {
                            id
                            title
                            author_id
                        }
                    }
                """,
                "mutation_example": """
                    mutation {
                        createPost(input: {
                            title: "My Post"
                            content: "Post content"
                            author_id: 1
                        }) {
                            id
                            title
                        }
                    }
                """,
            }
        }
    }


# Test data endpoint (for demonstration)
@app.post("/seed")
def seed_data(db: Session = Depends(get_db)):
    """Seed database with test data."""
    # Clear existing data
    db.query(Post).delete()

    # Add sample posts
    posts = [
        Post(id=1, title="Admin's Post", content="Content by admin", author_id=1, status="published"),
        Post(id=2, title="Editor's Post", content="Content by editor", author_id=2, status="published"),
        Post(id=3, title="Author's Post", content="Content by author", author_id=4, status="draft"),
        Post(id=4, title="Another Post", content="More content", author_id=4, status="published"),
    ]

    for post in posts:
        db.add(post)

    db.commit()

    return {"message": f"Seeded {len(posts)} posts"}


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*80)
    print("RBAC Example Server")
    print("="*80)
    print("\nAvailable tokens for testing:")
    print("  - admin_token: Full access (CRUD)")
    print("  - editor_token: Read and Update")
    print("  - author_token: Create and Read")
    print("  - viewer_token: Read only")
    print("\nUsage:")
    print("  curl -H 'Authorization: Bearer admin_token' http://127.0.0.1:8000/posts")
    print("\nEndpoints:")
    print("  - REST API: http://127.0.0.1:8000/posts")
    print("  - GraphQL: http://127.0.0.1:8000/graphql")
    print("  - API Docs: http://127.0.0.1:8000/docs")
    print("  - Seed Data: POST http://127.0.0.1:8000/seed")
    print("\n" + "="*80 + "\n")

    uvicorn.run(app, host="127.0.0.1", port=8000)
