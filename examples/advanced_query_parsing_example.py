"""
Advanced Query Parsing example for Basilisk - Phase 3 Features.

This example demonstrates the advanced query parsing capabilities for REST APIs:
1. Filtering with multiple values per field
2. Field selection with aliases
3. Aggregation functions (count, sum, avg, min, max)
4. Ordering (single and multiple fields)
5. Grouping

To run this example:
    1. Install basilisk: pip install -e .
    2. Run the server: python examples/advanced_query_parsing_example.py
    3. Open http://localhost:8000/docs for interactive API docs
    4. Try the query examples below!

Requirements:
    pip install fastapi sqlalchemy pydantic uvicorn
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

SQLALCHEMY_DATABASE_URL = "sqlite:///./example_advanced_query.db"

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


class Product(Base):
    """
    Product model with various fields for demonstrating query features.
    """

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    brand = Column(String, nullable=True, index=True)
    stock = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    status = Column(String, default="active", index=True)  # active, inactive, discontinued


# ============================================================================
# Pydantic Schemas
# ============================================================================


class ProductCreate(BaseModel):
    """Schema for creating a product."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    brand: str | None = None
    stock: int = Field(default=0, ge=0)
    rating: float = Field(default=0.0, ge=0, le=5)
    status: str = Field(default="active")


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    price: float | None = Field(None, gt=0)
    category: str | None = Field(None, min_length=1, max_length=100)
    brand: str | None = None
    stock: int | None = Field(None, ge=0)
    rating: float | None = Field(None, ge=0, le=5)
    status: str | None = None


class ProductResponse(BaseModel):
    """Schema for product responses."""

    id: int
    name: str
    description: str | None
    price: float
    category: str
    brand: str | None
    stock: int
    rating: float
    status: str

    model_config = {"from_attributes": True}


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Basilisk Advanced Query Parsing Example",
    description="Demonstrates Phase 3 advanced query parsing features for REST APIs",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Create database tables
Base.metadata.create_all(bind=engine)

# ============================================================================
# REST CRUD Router
# ============================================================================

product_router = CRUDRouter(
    model=Product,
    create_schema=ProductCreate,
    update_schema=ProductUpdate,
    response_schema=ProductResponse,
    get_db=get_db,
    prefix="/products",
    tags=["Products"],
)

app.include_router(product_router.router)


# ============================================================================
# Additional Endpoints
# ============================================================================


@app.get("/", tags=["Root"])
def read_root():
    """Welcome endpoint with comprehensive query examples."""
    return {
        "message": "Advanced Query Parsing Example - Phase 3 Features",
        "documentation": "/docs",
        "seed_data": "POST /seed to populate database with test data",
        "features": {
            "filtering": "Multiple values per field with OR logic within field, AND logic across fields",
            "field_selection": "Select specific fields with optional aliases",
            "aggregation": "count, sum, avg, min, max functions with grouping",
            "ordering": "Sort by single or multiple fields (asc/desc)",
            "grouping": "Group results by one or more fields",
        },
        "query_examples": {
            "1_basic_list": {
                "url": "/products/",
                "description": "List all products with default pagination",
            },
            "2_filtering_single_value": {
                "url": "/products/?category=Electronics",
                "description": "Filter by single value (exact match)",
            },
            "3_filtering_multiple_values": {
                "url": "/products/?status=active,inactive",
                "description": "Filter by multiple values (OR logic within field)",
            },
            "4_filtering_multiple_fields": {
                "url": "/products/?category=Electronics&status=active,inactive",
                "description": "Filter by multiple fields (AND logic across fields)",
            },
            "5_field_selection": {
                "url": "/products/?select=id,name,price",
                "description": "Select specific fields only",
            },
            "6_field_selection_with_alias": {
                "url": "/products/?select=name;product_name,price;cost",
                "description": "Select fields with aliases (use ; or 'as')",
            },
            "7_ordering_single": {
                "url": "/products/?orderBy=price:asc",
                "description": "Order by single field ascending",
            },
            "8_ordering_multiple": {
                "url": "/products/?orderBy=category:asc,price:desc",
                "description": "Order by multiple fields",
            },
            "9_aggregation_count": {
                "url": "/products/?select=category,count(id);total&groupBy=category",
                "description": "Count products per category",
            },
            "10_aggregation_avg_price": {
                "url": "/products/?select=category,avg(price);avg_price&groupBy=category",
                "description": "Average price per category",
            },
            "11_aggregation_sum": {
                "url": "/products/?select=brand,sum(stock);total_stock&groupBy=brand",
                "description": "Total stock per brand",
            },
            "12_complex_query": {
                "url": "/products/?category=Electronics,Books&status=active&select=name,price,category&orderBy=price:desc&skip=0&limit=10",
                "description": "Complex query combining filtering, selection, ordering, and pagination",
            },
            "13_multiple_grouping": {
                "url": "/products/?select=category,status,count(id);total&groupBy=category,status",
                "description": "Group by multiple fields (category and status)",
            },
            "14_multiple_aggregations": {
                "url": "/products/?select=category,count(id);total,avg(price);avg_price,sum(stock);total_stock&groupBy=category",
                "description": "Multiple aggregation functions in one query",
            },
        },
        "security_features": [
            "SQL injection prevention through whitelist validation",
            "Column name validation against model attributes",
            "Parameterized queries via SQLAlchemy",
            "Aggregation function name validation",
            "Alphanumeric validation for aliases",
        ],
        "tips": [
            "Use ; or 'as' for field aliases: ?select=name;product_name",
            "Comma separates multiple values within a field (OR logic)",
            "Ampersand separates different fields (AND logic)",
            "Aggregation requires groupBy parameter",
            "Visit /docs for interactive API testing",
        ],
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "basilisk-query-parsing-example"}


# ============================================================================
# Seed Data Function
# ============================================================================


@app.post("/seed", tags=["Database"])
def seed_database():
    """Seed the database with diverse test data for demonstrating query features."""
    db = next(get_db())

    try:
        # Clear existing data
        db.query(Product).delete()
        db.commit()

        # Create diverse products across categories
        products = [
            # Electronics - Active
            Product(
                name="Laptop Pro 15",
                description="High-performance laptop with 16GB RAM",
                price=1299.99,
                category="Electronics",
                brand="TechBrand",
                stock=50,
                rating=4.5,
                status="active",
            ),
            Product(
                name="Smartphone X",
                description="Latest flagship smartphone",
                price=899.99,
                category="Electronics",
                brand="PhoneCorp",
                stock=100,
                rating=4.7,
                status="active",
            ),
            Product(
                name="Wireless Headphones",
                description="Noise-cancelling over-ear headphones",
                price=299.99,
                category="Electronics",
                brand="AudioTech",
                stock=75,
                rating=4.6,
                status="active",
            ),
            Product(
                name="4K Monitor",
                description="27-inch 4K display",
                price=449.99,
                category="Electronics",
                brand="DisplayCo",
                stock=30,
                rating=4.4,
                status="active",
            ),
            # Electronics - Inactive
            Product(
                name="Old Tablet",
                description="Previous generation tablet",
                price=199.99,
                category="Electronics",
                brand="TechBrand",
                stock=5,
                rating=3.8,
                status="inactive",
            ),
            # Books - Active
            Product(
                name="Python Programming Guide",
                description="Comprehensive Python book",
                price=49.99,
                category="Books",
                brand="TechPublishers",
                stock=200,
                rating=4.8,
                status="active",
            ),
            Product(
                name="Web Development Mastery",
                description="Modern web development techniques",
                price=59.99,
                category="Books",
                brand="CodeBooks",
                stock=150,
                rating=4.6,
                status="active",
            ),
            Product(
                name="Data Science Handbook",
                description="Practical data science with Python",
                price=69.99,
                category="Books",
                brand="DataPress",
                stock=100,
                rating=4.7,
                status="active",
            ),
            # Clothing - Active
            Product(
                name="Cotton T-Shirt",
                description="Comfortable cotton t-shirt",
                price=19.99,
                category="Clothing",
                brand="FashionBrand",
                stock=500,
                rating=4.2,
                status="active",
            ),
            Product(
                name="Denim Jeans",
                description="Classic blue jeans",
                price=49.99,
                category="Clothing",
                brand="DenimCo",
                stock=300,
                rating=4.3,
                status="active",
            ),
            Product(
                name="Winter Jacket",
                description="Warm winter jacket",
                price=129.99,
                category="Clothing",
                brand="OutdoorWear",
                stock=100,
                rating=4.5,
                status="active",
            ),
            # Clothing - Discontinued
            Product(
                name="Summer Shorts (2020)",
                description="Last season's shorts",
                price=24.99,
                category="Clothing",
                brand="FashionBrand",
                stock=10,
                rating=4.0,
                status="discontinued",
            ),
            # Home & Garden - Active
            Product(
                name="Coffee Maker Deluxe",
                description="Programmable coffee maker",
                price=79.99,
                category="Home",
                brand="HomeTech",
                stock=80,
                rating=4.4,
                status="active",
            ),
            Product(
                name="Blender Pro",
                description="High-speed blender",
                price=99.99,
                category="Home",
                brand="KitchenMaster",
                stock=60,
                rating=4.5,
                status="active",
            ),
            Product(
                name="Robot Vacuum",
                description="Smart robot vacuum cleaner",
                price=299.99,
                category="Home",
                brand="HomeTech",
                stock=40,
                rating=4.6,
                status="active",
            ),
            # Sports - Active
            Product(
                name="Yoga Mat Premium",
                description="Non-slip yoga mat",
                price=29.99,
                category="Sports",
                brand="FitGear",
                stock=200,
                rating=4.5,
                status="active",
            ),
            Product(
                name="Adjustable Dumbbells",
                description="5-50 lbs adjustable dumbbells",
                price=249.99,
                category="Sports",
                brand="StrengthCo",
                stock=50,
                rating=4.7,
                status="active",
            ),
            Product(
                name="Running Shoes",
                description="Lightweight running shoes",
                price=89.99,
                category="Sports",
                brand="RunFast",
                stock=150,
                rating=4.6,
                status="active",
            ),
            # Sports - Inactive
            Product(
                name="Old Exercise Bike",
                description="Previous model exercise bike",
                price=399.99,
                category="Sports",
                brand="FitGear",
                stock=5,
                rating=3.9,
                status="inactive",
            ),
        ]

        for product in products:
            db.add(product)

        db.commit()

        # Get statistics
        total = len(products)
        categories = db.query(Product.category).distinct().count()
        brands = db.query(Product.brand).distinct().count()
        statuses = db.query(Product.status).distinct().count()

        return {
            "message": f"Successfully seeded {total} products!",
            "statistics": {
                "total_products": total,
                "unique_categories": categories,
                "unique_brands": brands,
                "unique_statuses": statuses,
            },
            "breakdown": {
                "Electronics": 5,
                "Books": 3,
                "Clothing": 4,
                "Home": 3,
                "Sports": 4,
            },
            "status_breakdown": {
                "active": 16,
                "inactive": 2,
                "discontinued": 1,
            },
            "next_steps": [
                "Visit /docs to explore the API interactively",
                "Try query examples from the root endpoint /",
                "Experiment with different query parameter combinations",
            ],
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e), "message": "Failed to seed database"}
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
    print("Basilisk Advanced Query Parsing Example - Phase 3")
    print("=" * 80)
    print("\nPhase 3 Features Demonstrated:")
    print("  - Filtering: Multiple values per field (?status=active,inactive)")
    print("  - Field Selection: Choose specific fields (?select=id,name,price)")
    print("  - Aliases: Rename fields in output (?select=name;product_name)")
    print("  - Aggregation: count, sum, avg, min, max functions")
    print("  - Ordering: Single or multiple fields (?orderBy=price:desc)")
    print("  - Grouping: Group by one or more fields (?groupBy=category)")
    print("\nSecurity Features:")
    print("  - SQL injection prevention")
    print("  - Column name validation")
    print("  - Parameterized queries")
    print("\nEndpoints:")
    print("  - Interactive Docs: http://localhost:8000/docs")
    print("  - API Root: http://localhost:8000/")
    print("  - Products: http://localhost:8000/products/")
    print("  - Seed Data: POST http://localhost:8000/seed")
    print("\nQuick Start:")
    print("  1. POST http://localhost:8000/seed (create test data)")
    print("  2. Visit http://localhost:8000/ (see query examples)")
    print("  3. Try queries at http://localhost:8000/docs")
    print("\nExample Queries:")
    print("  - Filter: /products/?category=Electronics&status=active")
    print("  - Select: /products/?select=name,price,category")
    print("  - Order: /products/?orderBy=price:desc")
    print("  - Aggregate: /products/?select=category,count(id);total&groupBy=category")
    print("\n" + "=" * 80 + "\n")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
