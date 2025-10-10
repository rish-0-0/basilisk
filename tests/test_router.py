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
