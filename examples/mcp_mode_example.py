"""
MCP (Model Context Protocol) Mode Example for Basilisk.

This example demonstrates how to enable MCP mode, which provides specialized
routes for AI agents to understand and interact with your API.

MCP mode adds /.mcp/ endpoints that provide:
- Comprehensive API documentation
- Usage examples
- Schema information
- Capability descriptions
- Best practices guide

Perfect for AI agents that need to understand your API structure!

To run this example:
    1. Install basilisk: pip install -e .
    2. Run the server: python examples/mcp_mode_example.py
    3. Try the MCP endpoints:
       - http://localhost:8000/products/.mcp/overview
       - http://localhost:8000/products/.mcp/schema
       - http://localhost:8000/products/.mcp/examples
       - http://localhost:8000/products/.mcp/capabilities
       - http://localhost:8000/products/.mcp/guide
"""

from fastapi import FastAPI
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field

from basilisk import CRUDRouter

# ============================================================================
# Database Setup
# ============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./example_mcp_mode.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
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


class Product(Base):
    """Product model for e-commerce."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    stock = Column(Integer, default=0)
    rating = Column(Float, default=0.0)


# ============================================================================
# Pydantic Schemas
# ============================================================================


class ProductCreate(BaseModel):
    """Schema for creating a product."""

    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: str | None = Field(None, description="Product description")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")
    stock: int = Field(default=0, ge=0, description="Available stock quantity")
    rating: float = Field(default=0.0, ge=0, le=5, description="Product rating (0-5)")


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: str | None = Field(None, min_length=1, max_length=200, description="Product name")
    description: str | None = Field(None, description="Product description")
    price: float | None = Field(None, gt=0, description="Product price (must be positive)")
    category: str | None = Field(None, min_length=1, max_length=100, description="Product category")
    stock: int | None = Field(None, ge=0, description="Available stock quantity")
    rating: float | None = Field(None, ge=0, le=5, description="Product rating (0-5)")


class ProductResponse(BaseModel):
    """Schema for product responses."""

    id: int = Field(..., description="Unique product ID")
    name: str = Field(..., description="Product name")
    description: str | None = Field(None, description="Product description")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    stock: int = Field(..., description="Available stock quantity")
    rating: float = Field(..., description="Product rating (0-5)")

    model_config = {"from_attributes": True}


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Basilisk MCP Mode Example",
    description="Demonstrates MCP (Model Context Protocol) mode for AI agent integration",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Create database tables
Base.metadata.create_all(bind=engine)


# ============================================================================
# CRUD Router with MCP Mode ENABLED
# ============================================================================

product_router = CRUDRouter(
    model=Product,
    create_schema=ProductCreate,
    update_schema=ProductUpdate,
    response_schema=ProductResponse,
    get_db=get_db,
    prefix="/products",
    tags=["Products"],
    enable_mcp=True,  # 🎯 ENABLE MCP MODE - This adds /.mcp/ endpoints
)

app.include_router(product_router.router)


# ============================================================================
# Additional Endpoints
# ============================================================================


@app.get("/", tags=["Root"])
def read_root():
    """Welcome endpoint with MCP mode information."""
    return {
        "message": "Welcome to Basilisk MCP Mode Example!",
        "description": "This example demonstrates MCP (Model Context Protocol) mode for AI agents",
        "version": "0.3.0",
        "standard_api": {
            "products": "/products/",
            "swagger_docs": "/docs",
            "openapi_schema": "/openapi.json",
        },
        "mcp_endpoints": {
            "description": "Special endpoints for AI agents to understand the API",
            "overview": {
                "url": "/products/.mcp/overview",
                "description": "Complete API overview with all information",
            },
            "schema": {
                "url": "/products/.mcp/schema",
                "description": "Detailed schema information for all operations",
            },
            "examples": {
                "url": "/products/.mcp/examples",
                "description": "Comprehensive usage examples for each endpoint",
            },
            "capabilities": {
                "url": "/products/.mcp/capabilities",
                "description": "List of all supported features and operations",
            },
            "guide": {
                "url": "/products/.mcp/guide",
                "description": "Best practices guide for AI agents",
            },
        },
        "what_is_mcp": {
            "description": "MCP (Model Context Protocol) provides AI agents with comprehensive API context",
            "benefits": [
                "AI agents can understand API structure without manual prompting",
                "Comprehensive documentation in machine-readable format",
                "Examples show real-world usage patterns",
                "Capabilities describe what's possible",
                "Guides provide best practices",
            ],
            "use_cases": [
                "AI assistants helping users interact with your API",
                "Automated testing and validation",
                "API discovery and exploration",
                "Documentation generation",
                "Client SDK generation",
            ],
        },
        "quick_start": {
            "1": "Visit /products/.mcp/overview to see all MCP data at once",
            "2": "Check /products/.mcp/examples for usage patterns",
            "3": "Review /products/.mcp/guide for best practices",
            "4": "Use /products/ for actual API operations",
        },
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "basilisk-mcp-example", "mcp_enabled": True}


# ============================================================================
# Seed Data Function
# ============================================================================


@app.post("/seed", tags=["Database"])
def seed_database():
    """Seed the database with example data."""
    db = next(get_db())

    try:
        # Clear existing data
        db.query(Product).delete()
        db.commit()

        # Create sample products
        products = [
            Product(
                name="Laptop Pro 15",
                description="High-performance laptop",
                price=1299.99,
                category="Electronics",
                stock=50,
                rating=4.5,
            ),
            Product(
                name="Wireless Mouse",
                description="Ergonomic wireless mouse",
                price=29.99,
                category="Electronics",
                stock=200,
                rating=4.3,
            ),
            Product(
                name="Python Programming Guide",
                description="Comprehensive Python book",
                price=49.99,
                category="Books",
                stock=100,
                rating=4.8,
            ),
            Product(
                name="Coffee Maker",
                description="Programmable coffee maker",
                price=79.99,
                category="Home",
                stock=75,
                rating=4.4,
            ),
            Product(
                name="Yoga Mat",
                description="Non-slip yoga mat",
                price=29.99,
                category="Sports",
                stock=150,
                rating=4.6,
            ),
        ]

        for product in products:
            db.add(product)

        db.commit()

        return {
            "message": f"Successfully seeded {len(products)} products",
            "next_steps": [
                "Visit /products/ to see all products",
                "Try /products/.mcp/overview for MCP context",
                "Use /products/.mcp/examples for usage patterns",
            ],
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

    print("\n" + "=" * 80)
    print("Basilisk MCP Mode Example")
    print("=" * 80)
    print("\nMCP (Model Context Protocol) Routes:")
    print("  - Overview: http://localhost:8000/products/.mcp/overview")
    print("  - Schema: http://localhost:8000/products/.mcp/schema")
    print("  - Examples: http://localhost:8000/products/.mcp/examples")
    print("  - Capabilities: http://localhost:8000/products/.mcp/capabilities")
    print("  - Guide: http://localhost:8000/products/.mcp/guide")
    print("\nStandard API Routes:")
    print("  - Products API: http://localhost:8000/products/")
    print("  - Swagger Docs: http://localhost:8000/docs")
    print("  - Home: http://localhost:8000/")
    print("\nQuick Start:")
    print("  1. POST http://localhost:8000/seed (create test data)")
    print("  2. GET http://localhost:8000/products/.mcp/overview (AI agent context)")
    print("  3. GET http://localhost:8000/products/ (list products)")
    print("\nWhat is MCP?")
    print("  MCP mode provides AI agents with comprehensive API context,")
    print("  including schemas, examples, capabilities, and best practices.")
    print("  It's like having an API handbook specifically for AI agents!")
    print("\n" + "=" * 80 + "\n")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
