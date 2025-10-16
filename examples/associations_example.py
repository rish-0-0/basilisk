"""
Comprehensive example demonstrating all association (relationship) types in Basilisk.

This example shows how to use Basilisk with SQLAlchemy relationships:
- One-to-Many: User has many Posts
- Many-to-One: Post belongs to User
- One-to-One: User has one Profile
- Many-to-Many: Post has many Tags, Tag has many Posts

To run this example:
    1. Install basilisk: pip install -e .
    2. Run the server: python examples/associations_example.py
    3. Open http://localhost:8000/docs for REST API
    4. Open http://localhost:8000/graphql for GraphQL playground

Features demonstrated:
- Opt-in associations support with enable_associations=True
- REST API with ?include parameter for eager loading
- GraphQL API with automatic nested resolvers
- All four relationship types
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from basilisk import CRUDRouter, GraphQLCRUDRouter

# ============================================================================
# Database Setup
# ============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./example_associations.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True,
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
# SQLAlchemy Models with All Relationship Types
# ============================================================================

# Many-to-Many: Association table for Post <-> Tag
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    """
    User model with relationships:
    - One-to-Many: has many posts
    - One-to-One: has one profile
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)

    # One-to-Many: User has many Posts
    posts = relationship("Post", back_populates="author")

    # One-to-One: User has one Profile
    profile = relationship("Profile", back_populates="user", uselist=False)


class Post(Base):
    """
    Post model with relationships:
    - Many-to-One: belongs to a user (author)
    - Many-to-Many: has many tags
    """

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Many-to-One: Post belongs to User
    author = relationship("User", back_populates="posts")

    # Many-to-Many: Post has many Tags
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")


class Profile(Base):
    """
    Profile model with relationship:
    - One-to-One: belongs to a user
    """

    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    website = Column(String, nullable=True)

    # One-to-One: Profile belongs to User
    user = relationship("User", back_populates="profile")


class Tag(Base):
    """
    Tag model with relationship:
    - Many-to-Many: has many posts
    """

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    # Many-to-Many: Tag has many Posts
    posts = relationship("Post", secondary=post_tags, back_populates="tags")


# ============================================================================
# Pydantic Schemas
# ============================================================================

# User schemas
class UserCreate(BaseModel):
    """Schema for creating a user."""

    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(...)


class UserResponse(BaseModel):
    """Schema for user responses (with associations if requested)."""

    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


# Post schemas
class PostCreate(BaseModel):
    """Schema for creating a post."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    author_id: int = Field(..., description="ID of the author (user)")


class PostResponse(BaseModel):
    """Schema for post responses."""

    id: int
    title: str
    content: str
    author_id: int

    model_config = {"from_attributes": True}


# Profile schemas
class ProfileCreate(BaseModel):
    """Schema for creating a profile."""

    user_id: int = Field(..., description="ID of the user")
    bio: str | None = None
    website: str | None = None


class ProfileResponse(BaseModel):
    """Schema for profile responses."""

    id: int
    user_id: int
    bio: str | None
    website: str | None

    model_config = {"from_attributes": True}


# Tag schemas
class TagCreate(BaseModel):
    """Schema for creating a tag."""

    name: str = Field(..., min_length=1, max_length=50)


class TagResponse(BaseModel):
    """Schema for tag responses."""

    id: int
    name: str

    model_config = {"from_attributes": True}


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Basilisk Associations Example",
    description="Demonstrates all association/relationship types with opt-in support",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Create database tables
Base.metadata.create_all(bind=engine)

# ============================================================================
# REST CRUD Routers with Associations ENABLED
# ============================================================================

# User router with associations enabled
user_router = CRUDRouter(
    model=User,
    create_schema=UserCreate,
    response_schema=UserResponse,
    get_db=get_db,
    prefix="/users",
    tags=["Users"],
    enable_associations=True,  # OPT-IN: Enable association support
)

# Post router with associations enabled
post_router = CRUDRouter(
    model=Post,
    create_schema=PostCreate,
    response_schema=PostResponse,
    get_db=get_db,
    prefix="/posts",
    tags=["Posts"],
    enable_associations=True,  # OPT-IN: Enable association support
)

# Profile router with associations enabled
profile_router = CRUDRouter(
    model=Profile,
    create_schema=ProfileCreate,
    response_schema=ProfileResponse,
    get_db=get_db,
    prefix="/profiles",
    tags=["Profiles"],
    enable_associations=True,  # OPT-IN: Enable association support
)

# Tag router with associations enabled
tag_router = CRUDRouter(
    model=Tag,
    create_schema=TagCreate,
    response_schema=TagResponse,
    get_db=get_db,
    prefix="/tags",
    tags=["Tags"],
    enable_associations=True,  # OPT-IN: Enable association support
)

# Include routers
app.include_router(user_router.router)
app.include_router(post_router.router)
app.include_router(profile_router.router)
app.include_router(tag_router.router)

# ============================================================================
# GraphQL Router with Associations ENABLED
# ============================================================================

# User GraphQL
user_graphql = GraphQLCRUDRouter(
    model=User,
    create_schema=UserCreate,
    response_schema=UserResponse,
    get_db=get_db,
    resource_name="User",
    enable_associations=True,  # OPT-IN: Enable association support
)

# Post GraphQL
post_graphql = GraphQLCRUDRouter(
    model=Post,
    create_schema=PostCreate,
    response_schema=PostResponse,
    get_db=get_db,
    resource_name="Post",
    enable_associations=True,  # OPT-IN: Enable association support
)

# Mount GraphQL apps
app.mount("/graphql/users", user_graphql.app)
app.mount("/graphql/posts", post_graphql.app)

# ============================================================================
# Additional Endpoints
# ============================================================================


@app.get("/", tags=["Root"])
def read_root():
    """Welcome endpoint with usage examples."""
    return {
        "message": "Welcome to Basilisk Associations Example!",
        "version": "0.3.0",
        "features": [
            "One-to-Many: User -> Posts",
            "Many-to-One: Post -> User (author)",
            "One-to-One: User -> Profile",
            "Many-to-Many: Post <-> Tags",
        ],
        "rest_api_examples": {
            "list_users": "/users/",
            "list_users_with_posts": "/users/?include=posts",
            "list_users_with_posts_and_profile": "/users/?include=posts,profile",
            "get_user_with_associations": "/users/1?include=posts,profile",
            "list_posts_with_author": "/posts/?include=author",
            "list_posts_with_author_and_tags": "/posts/?include=author,tags",
        },
        "graphql_api": {
            "users": "/graphql/users",
            "posts": "/graphql/posts",
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
        },
        "note": "Associations are OPT-IN via enable_associations=True",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "basilisk-associations-example"}


# ============================================================================
# Seed Data Function
# ============================================================================


@app.post("/seed", tags=["Database"])
def seed_database():
    """Seed the database with example data demonstrating all relationship types."""
    db = next(get_db())

    try:
        # Clear existing data
        db.query(Post).delete()
        db.query(Profile).delete()
        db.query(User).delete()
        db.query(Tag).delete()
        db.commit()

        # Create users
        user1 = User(name="Alice Johnson", email="alice@example.com")
        user2 = User(name="Bob Smith", email="bob@example.com")
        db.add_all([user1, user2])
        db.commit()

        # Create profiles (One-to-One)
        profile1 = Profile(
            user_id=user1.id, bio="Software engineer and tech enthusiast", website="https://alice.dev"
        )
        profile2 = Profile(
            user_id=user2.id, bio="Writer and blogger", website="https://bobwrites.com"
        )
        db.add_all([profile1, profile2])
        db.commit()

        # Create tags
        tag_python = Tag(name="Python")
        tag_fastapi = Tag(name="FastAPI")
        tag_sqlalchemy = Tag(name="SQLAlchemy")
        tag_web = Tag(name="Web Development")
        db.add_all([tag_python, tag_fastapi, tag_sqlalchemy, tag_web])
        db.commit()

        # Create posts (One-to-Many from User, Many-to-Many with Tags)
        post1 = Post(
            title="Getting Started with FastAPI",
            content="FastAPI is a modern, fast web framework for building APIs with Python 3.7+...",
            author_id=user1.id,
        )
        post1.tags.extend([tag_python, tag_fastapi, tag_web])

        post2 = Post(
            title="SQLAlchemy Best Practices",
            content="Learn how to use SQLAlchemy effectively in your projects...",
            author_id=user1.id,
        )
        post2.tags.extend([tag_python, tag_sqlalchemy])

        post3 = Post(
            title="Building REST APIs",
            content="A comprehensive guide to building RESTful APIs...",
            author_id=user2.id,
        )
        post3.tags.extend([tag_web])

        db.add_all([post1, post2, post3])
        db.commit()

        return {
            "message": "Database seeded successfully!",
            "data": {
                "users": 2,
                "profiles": 2,
                "posts": 3,
                "tags": 4,
            },
            "relationships": {
                "alice_posts": 2,
                "bob_posts": 1,
                "post1_tags": 3,
                "post2_tags": 2,
                "post3_tags": 1,
            },
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


# ============================================================================
# Run the Server
# ============================================================================

if __name__ == "__main__":
    import sys

    import uvicorn

    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("\n" + "=" * 70)
    print("Basilisk Associations Example Server")
    print("=" * 70)
    print(f"\nInteractive API Docs: http://localhost:8000/docs")
    print(f"ReDoc Documentation: http://localhost:8000/redoc")
    print(f"GraphQL (Users): http://localhost:8000/graphql/users")
    print(f"GraphQL (Posts): http://localhost:8000/graphql/posts")
    print(f"\nSeed Data: POST http://localhost:8000/seed")
    print(f"\nExample Queries with Associations:")
    print(f"  - GET /users/?include=posts,profile")
    print(f"  - GET /posts/?include=author,tags")
    print(f"  - GET /users/1?include=posts.tags,profile")
    print("\n" + "=" * 70 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
