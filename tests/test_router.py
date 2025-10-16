"""Test route generation - TDD approach."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel


# Test database setup
# Use file-based SQLite for testing to avoid threading issues
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_basilisk.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Test model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)


# Test schemas
class UserCreate(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_router_generation():
    """Test that we can generate a router and it creates the expected routes."""
    from basilisk import CRUDRouter

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create FastAPI app
    app = FastAPI()

    # Generate router using basilisk
    crud_router = CRUDRouter(
        model=User,
        create_schema=UserCreate,
        response_schema=UserResponse,
        get_db=get_db,
        prefix="/users",
    )

    # Include the router
    app.include_router(crud_router.router)

    # Test that routes are created
    client = TestClient(app)

    # Test the list endpoint exists and returns empty list
    response = client.get("/users/")
    assert response.status_code == 200
    assert response.json() == []

    # Clean up
    Base.metadata.drop_all(bind=engine)


def test_get_single_user():
    """Test GET /users/{id} endpoint - retrieve a single user by ID."""
    from basilisk import CRUDRouter

    # Create tables
    Base.metadata.create_all(bind=engine)

    try:
        # Create FastAPI app
        app = FastAPI()

        # Generate router using basilisk
        crud_router = CRUDRouter(
            model=User,
            create_schema=UserCreate,
            response_schema=UserResponse,
            get_db=get_db,
            prefix="/users",
        )

        # Include the router
        app.include_router(crud_router.router)

        client = TestClient(app)

        # First, create a user directly in the database
        db = SessionLocal()
        user = User(name="John Doe", email="john@example.com")
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
        db.close()

        # Test getting the user by ID
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == user_id
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"

        # Test getting non-existent user (should return 404)
        response = client.get("/users/99999")
        assert response.status_code == 404

    finally:
        # Clean up
        Base.metadata.drop_all(bind=engine)


def test_create_user():
    """Test POST /users/ endpoint - create a new user."""
    from basilisk import CRUDRouter

    # Create tables
    Base.metadata.create_all(bind=engine)

    try:
        # Create FastAPI app
        app = FastAPI()

        # Generate router using basilisk
        crud_router = CRUDRouter(
            model=User,
            create_schema=UserCreate,
            response_schema=UserResponse,
            get_db=get_db,
            prefix="/users",
        )

        # Include the router
        app.include_router(crud_router.router)

        client = TestClient(app)

        # Test creating a new user
        user_data = {
            "name": "Jane Smith",
            "email": "jane@example.com"
        }

        response = client.post("/users/", json=user_data)
        assert response.status_code == 201  # Created

        data = response.json()
        assert data["name"] == "Jane Smith"
        assert data["email"] == "jane@example.com"
        assert "id" in data
        assert isinstance(data["id"], int)

        # Verify user was actually created in database
        user_id = data["id"]
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json() == data

        # Test creating user with duplicate email (should fail)
        duplicate_response = client.post("/users/", json=user_data)
        assert duplicate_response.status_code == 400  # Bad request

    finally:
        # Clean up
        Base.metadata.drop_all(bind=engine)


def test_update_user():
    """Test PUT /users/{id} endpoint - update an existing user."""
    from basilisk import CRUDRouter

    # Create tables
    Base.metadata.create_all(bind=engine)

    try:
        # Create FastAPI app
        app = FastAPI()

        # Generate router using basilisk
        crud_router = CRUDRouter(
            model=User,
            create_schema=UserCreate,
            update_schema=UserUpdate,
            response_schema=UserResponse,
            get_db=get_db,
            prefix="/users",
        )

        # Include the router
        app.include_router(crud_router.router)

        client = TestClient(app)

        # First, create a user
        user_data = {
            "name": "Original Name",
            "email": "original@example.com"
        }
        create_response = client.post("/users/", json=user_data)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        # Test full update
        update_data = {
            "name": "Updated Name",
            "email": "updated@example.com"
        }
        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == user_id
        assert data["name"] == "Updated Name"
        assert data["email"] == "updated@example.com"

        # Test partial update (only name)
        partial_update = {"name": "Partially Updated"}
        response = client.put(f"/users/{user_id}", json=partial_update)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Partially Updated"
        assert data["email"] == "updated@example.com"  # Should remain unchanged

        # Test updating non-existent user (should return 404)
        response = client.put("/users/99999", json=update_data)
        assert response.status_code == 404

        # Test updating with duplicate email
        # Create another user first
        another_user = {"name": "Another User", "email": "another@example.com"}
        client.post("/users/", json=another_user)

        # Try to update first user with email of second user
        duplicate_update = {"email": "another@example.com"}
        response = client.put(f"/users/{user_id}", json=duplicate_update)
        assert response.status_code == 400  # Should fail due to unique constraint

    finally:
        # Clean up
        Base.metadata.drop_all(bind=engine)


def test_delete_user():
    """Test DELETE /users/{id} endpoint - delete a user."""
    from basilisk import CRUDRouter

    # Create tables
    Base.metadata.create_all(bind=engine)

    try:
        # Create FastAPI app
        app = FastAPI()

        # Generate router using basilisk
        crud_router = CRUDRouter(
            model=User,
            create_schema=UserCreate,
            response_schema=UserResponse,
            get_db=get_db,
            prefix="/users",
        )

        # Include the router
        app.include_router(crud_router.router)

        client = TestClient(app)

        # First, create a user
        user_data = {
            "name": "To Be Deleted",
            "email": "delete@example.com"
        }
        create_response = client.post("/users/", json=user_data)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        # Verify user exists
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 200

        # Delete the user
        delete_response = client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 204  # No content

        # Verify user no longer exists
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

        # Test deleting non-existent user (should return 404)
        response = client.delete("/users/99999")
        assert response.status_code == 404

    finally:
        # Clean up
        Base.metadata.drop_all(bind=engine)


def test_list_users_pagination():
    """Test GET /users/ endpoint with pagination."""
    from basilisk import CRUDRouter

    # Create tables
    Base.metadata.create_all(bind=engine)

    try:
        # Create FastAPI app
        app = FastAPI()

        # Generate router using basilisk
        crud_router = CRUDRouter(
            model=User,
            create_schema=UserCreate,
            response_schema=UserResponse,
            get_db=get_db,
            prefix="/users",
        )

        # Include the router
        app.include_router(crud_router.router)

        client = TestClient(app)

        # Create multiple users
        for i in range(15):
            user_data = {
                "name": f"User {i}",
                "email": f"user{i}@example.com"
            }
            client.post("/users/", json=user_data)

        # Test default pagination (limit=100, skip=0)
        response = client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 15

        # Test with limit
        response = client.get("/users/?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # Test with skip
        response = client.get("/users/?skip=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # 15 total - 10 skipped = 5

        # Test with both limit and skip
        response = client.get("/users/?skip=5&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    finally:
        # Clean up
        Base.metadata.drop_all(bind=engine)



def test_list_users_with_filtering():
    """Test GET /users/ with query filtering."""
    from basilisk import CRUDRouter

    # Create tables
    Base.metadata.create_all(bind=engine)

    try:
        # Create FastAPI app
        app = FastAPI()

        # Generate router using basilisk
        crud_router = CRUDRouter(
            model=User,
            create_schema=UserCreate,
            response_schema=UserResponse,
            get_db=get_db,
            prefix="/users",
        )

        # Include the router
        app.include_router(crud_router.router)

        client = TestClient(app)

        # Create test users
        client.post("/users/", json={"name": "Alice", "email": "alice@example.com"})
        client.post("/users/", json={"name": "Bob", "email": "bob@example.com"})
        client.post("/users/", json={"name": "Alice", "email": "alice2@example.com"})

        # Test filtering by name
        response = client.get("/users/?name=Alice")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(user["name"] == "Alice" for user in data)

        # Test filtering by email
        response = client.get("/users/?email=bob@example.com")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "bob@example.com"

    finally:
        # Clean up
        Base.metadata.drop_all(bind=engine)


def test_list_users_with_ordering():
    """Test GET /users/ with ordering."""
    from basilisk import CRUDRouter

    # Create tables
    Base.metadata.create_all(bind=engine)

    try:
        # Create FastAPI app
        app = FastAPI()

        # Generate router using basilisk
        crud_router = CRUDRouter(
            model=User,
            create_schema=UserCreate,
            response_schema=UserResponse,
            get_db=get_db,
            prefix="/users",
        )

        # Include the router
        app.include_router(crud_router.router)

        client = TestClient(app)

        # Create test users
        client.post("/users/", json={"name": "Charlie", "email": "charlie@example.com"})
        client.post("/users/", json={"name": "Alice", "email": "alice@example.com"})
        client.post("/users/", json={"name": "Bob", "email": "bob@example.com"})

        # Test ordering by name ascending
        response = client.get("/users/?orderBy=name:asc")
        assert response.status_code == 200
        data = response.json()
        names = [user["name"] for user in data]
        assert names == sorted(names)
        assert names[0] == "Alice"

        # Test ordering by name descending
        response = client.get("/users/?orderBy=name:desc")
        assert response.status_code == 200
        data = response.json()
        names = [user["name"] for user in data]
        assert names == sorted(names, reverse=True)
        assert names[0] == "Charlie"

    finally:
        # Clean up
        Base.metadata.drop_all(bind=engine)

