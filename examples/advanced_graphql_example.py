"""
Advanced GraphQL example demonstrating Phase 4 features.

This example showcases:
1. Relay-style connection pagination
2. Advanced filtering with where clauses
3. Ordering and complex queries
4. GraphQL Playground integration

Requirements:
    pip install fastapi sqlalchemy pydantic ariadne uvicorn
"""

from fastapi import FastAPI
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

from basilisk import GraphQLCRUDRouter

# Database setup
Base = declarative_base()
engine = create_engine("sqlite:///./advanced_graphql.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# SQLAlchemy Model
class Product(Base):
    """Product model with various fields for demonstrating filters."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    stock = Column(Integer, default=0)
    rating = Column(Float, default=0.0)


# Pydantic Schemas
class ProductCreate(BaseModel):
    """Schema for creating a product."""
    name: str
    description: str
    price: float
    category: str
    stock: int = 0
    rating: float = 0.0


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category: str | None = None
    stock: int | None = None
    rating: float | None = None


class ProductResponse(BaseModel):
    """Schema for product responses."""
    id: int
    name: str
    description: str
    price: float
    category: str
    stock: int
    rating: float

    class Config:
        from_attributes = True


# Database dependency
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create FastAPI app
app = FastAPI(
    title="Advanced GraphQL Example",
    description="Demonstrating Relay pagination and advanced filtering",
    version="1.0.0",
)


# Create tables
Base.metadata.create_all(bind=engine)


# Create GraphQL router with all Phase 4 features
graphql_router = GraphQLCRUDRouter(
    model=Product,
    create_schema=ProductCreate,
    update_schema=ProductUpdate,
    response_schema=ProductResponse,
    get_db=get_db,
    resource_name="Product",
)

app.mount("/graphql", graphql_router.app)


# Root endpoint with usage examples
@app.get("/")
def read_root():
    """Root endpoint with API documentation."""
    return {
        "message": "Advanced GraphQL Example - Phase 4 Features",
        "graphql_endpoint": "/graphql",
        "features": {
            "relay_pagination": "Cursor-based pagination with edges, nodes, and pageInfo",
            "advanced_filtering": "WHERE clauses with comparison operators (eq, in, lt, gt, etc.)",
            "ordering": "Sort by multiple fields with asc/desc",
            "aggregation": "Count, sum, avg, min, max functions",
        },
        "example_queries": {
            "1_simple_list": """
query {
  products {
    id
    name
    price
  }
}
            """,
            "2_relay_pagination": """
query {
  productsConnection(first: 10, after: "cursor_here") {
    edges {
      node {
        id
        name
        price
      }
      cursor
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
    totalCount
  }
}
            """,
            "3_advanced_filtering_single": """
query {
  products(where: { price_lt: 100 }) {
    id
    name
    price
  }
}
            """,
            "4_advanced_filtering_multiple": """
query {
  products(where: {
    price_gte: 50
    price_lte: 200
    category: "Electronics"
  }) {
    id
    name
    price
    category
  }
}
            """,
            "5_filtering_with_in": """
query {
  products(where: {
    category_in: ["Electronics", "Books", "Clothing"]
    price_lt: 100
  }) {
    id
    name
    category
    price
  }
}
            """,
            "6_logical_operators_and": """
query {
  products(where: {
    AND: [
      { price_gte: 50 },
      { price_lte: 200 },
      { stock_gt: 0 }
    ]
  }) {
    id
    name
    price
    stock
  }
}
            """,
            "7_logical_operators_or": """
query {
  products(where: {
    OR: [
      { category: "Electronics" },
      { category: "Books" }
    ]
  }) {
    id
    name
    category
  }
}
            """,
            "8_complex_nested_filters": """
query {
  products(where: {
    AND: [
      {
        OR: [
          { category: "Electronics" },
          { category: "Computers" }
        ]
      },
      { price_lt: 500 },
      { stock_gt: 0 }
    ]
  }) {
    id
    name
    category
    price
    stock
  }
}
            """,
            "9_ordering": """
query {
  products(orderBy: ["price:asc", "rating:desc"]) {
    id
    name
    price
    rating
  }
}
            """,
            "10_pagination_with_filters_and_ordering": """
query {
  productsConnection(
    first: 10
    where: {
      category: "Electronics"
      price_lt: 1000
    }
    orderBy: ["price:desc"]
  ) {
    edges {
      node {
        id
        name
        price
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
            """,
        },
        "example_mutations": {
            "create": """
mutation {
  createProduct(input: {
    name: "Laptop"
    description: "High-performance laptop"
    price: 999.99
    category: "Electronics"
    stock: 50
    rating: 4.5
  }) {
    id
    name
    price
  }
}
            """,
            "update": """
mutation {
  updateProduct(id: 1, input: {
    price: 899.99
    stock: 45
  }) {
    id
    name
    price
    stock
  }
}
            """,
            "delete": """
mutation {
  deleteProduct(id: 1)
}
            """,
        },
        "testing": {
            "graphql_playground": "Visit /graphql for interactive GraphQL Playground",
            "seed_data": "POST /seed to populate database with test data",
        }
    }


# Seed data endpoint
@app.post("/seed")
def seed_data():
    """Seed database with test data."""
    from sqlalchemy.orm import Session

    db = SessionLocal()
    try:
        # Clear existing data
        db.query(Product).delete()

        # Add sample products across different categories
        products = [
            # Electronics
            Product(name="Laptop", description="High-performance laptop", price=999.99, category="Electronics", stock=50, rating=4.5),
            Product(name="Smartphone", description="Latest model smartphone", price=799.99, category="Electronics", stock=100, rating=4.7),
            Product(name="Tablet", description="10-inch tablet", price=499.99, category="Electronics", stock=75, rating=4.3),
            Product(name="Headphones", description="Noise-cancelling headphones", price=299.99, category="Electronics", stock=200, rating=4.6),
            Product(name="Smartwatch", description="Fitness tracking smartwatch", price=399.99, category="Electronics", stock=150, rating=4.4),

            # Books
            Product(name="Python Programming", description="Learn Python from scratch", price=49.99, category="Books", stock=500, rating=4.8),
            Product(name="Web Development", description="Modern web development guide", price=59.99, category="Books", stock=300, rating=4.6),
            Product(name="Data Science", description="Data science with Python", price=69.99, category="Books", stock=250, rating=4.7),

            # Clothing
            Product(name="T-Shirt", description="Cotton t-shirt", price=19.99, category="Clothing", stock=1000, rating=4.2),
            Product(name="Jeans", description="Denim jeans", price=49.99, category="Clothing", stock=500, rating=4.3),
            Product(name="Jacket", description="Winter jacket", price=129.99, category="Clothing", stock=200, rating=4.5),

            # Home & Garden
            Product(name="Coffee Maker", description="Programmable coffee maker", price=79.99, category="Home", stock=150, rating=4.4),
            Product(name="Blender", description="High-speed blender", price=99.99, category="Home", stock=100, rating=4.5),
            Product(name="Vacuum Cleaner", description="Robot vacuum", price=299.99, category="Home", stock=75, rating=4.6),

            # Sports
            Product(name="Yoga Mat", description="Non-slip yoga mat", price=29.99, category="Sports", stock=300, rating=4.5),
            Product(name="Dumbbells", description="Adjustable dumbbells", price=149.99, category="Sports", stock=100, rating=4.7),
        ]

        for product in products:
            db.add(product)

        db.commit()

        return {
            "message": f"Seeded {len(products)} products",
            "categories": ["Electronics", "Books", "Clothing", "Home", "Sports"],
            "total_products": len(products),
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*80)
    print("Advanced GraphQL Example - Phase 4 Features")
    print("="*80)
    print("\nFeatures Demonstrated:")
    print("  ✓ Relay-style connection pagination")
    print("  ✓ Advanced WHERE filtering (eq, in, lt, lte, gt, gte, not)")
    print("  ✓ Logical operators (AND, OR, NOT)")
    print("  ✓ Multiple field ordering")
    print("  ✓ Cursor-based pagination")
    print("\nEndpoints:")
    print("  - GraphQL Playground: http://127.0.0.1:8000/graphql")
    print("  - API Info: http://127.0.0.1:8000/")
    print("  - Seed Data: POST http://127.0.0.1:8000/seed")
    print("\nQuick Start:")
    print("  1. POST http://127.0.0.1:8000/seed (to create test data)")
    print("  2. Visit http://127.0.0.1:8000/graphql (GraphQL Playground)")
    print("  3. Try the example queries from http://127.0.0.1:8000/")
    print("\n" + "="*80 + "\n")

    uvicorn.run(app, host="127.0.0.1", port=8000)
