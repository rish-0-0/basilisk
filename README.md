# Basilisk

> **Petrify** = make solid/unchanging (REST API standards)

Auto-generate full-featured CRUD APIs from Pydantic models for FastAPI. Pass in a model, get REST and GraphQL routes with advanced querying, associations, RBAC, and AI agent integration.

## Features

### Core Features
- **Automatic REST API** - Full CRUD endpoints from Pydantic models
- **Automatic GraphQL API** - Queries and mutations with schema generation
- **Advanced Query Parsing** - Filtering, field selection, aggregation, ordering, grouping
- **Multi-Model Associations** - One-to-many, many-to-one, one-to-one, many-to-many (opt-in)
- **Role-Based Access Control** - Operation and resource-level permissions (opt-in)
- **MCP Mode** - AI agent integration endpoints for automated discovery (opt-in)
- **Security First** - SQL injection prevention, input validation, sanitization

### REST API Features
- CRUD operations (Create, Read, Update, Delete)
- Pagination (offset-based)
- Advanced filtering: `?status=active,pending&role=admin`
- Field selection: `?select=id,name,email`
- Aggregations: `?select=count(id) as total&groupBy=category`
- Ordering: `?orderBy=name:asc,created_at:desc`
- Include associations: `?include=posts,profile`

### GraphQL Features
- Full CRUD with queries and mutations
- Relay-style cursor pagination with connections
- Advanced WHERE filtering with operators (eq, in, lt, gte, etc.)
- Logical operators (AND, OR, NOT)
- Multi-field ordering
- Nested relationship resolvers (with associations enabled)

## Installation

```bash
pip install basilisk
```

For GraphQL support:
```bash
pip install "basilisk[graphql]"
```

## Quick Start

### Basic REST API

```python
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from pydantic import BaseModel
from basilisk import CRUDRouter

# SQLAlchemy Model
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    category = Column(String, nullable=False)

# Pydantic Schemas
class ProductCreate(BaseModel):
    name: str
    price: int
    category: str

class ProductResponse(BaseModel):
    id: int
    name: str
    price: int
    category: str

    model_config = {"from_attributes": True}

# Database Setup
engine = create_engine("sqlite:///./products.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create FastAPI App with Auto-Generated Routes
app = FastAPI()

router = CRUDRouter(
    model=Product,
    create_schema=ProductCreate,
    response_schema=ProductResponse,
    get_db=get_db,
)

app.include_router(router, prefix="/products", tags=["products"])
```

**Generated Endpoints:**
- `GET /products/` - List all products with filtering
- `GET /products/{id}` - Get single product
- `POST /products/` - Create product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product

### Advanced Query Examples

```bash
# Filter by multiple values (OR within field, AND across fields)
GET /products/?category=electronics,books&status=active

# Select specific fields with aliases
GET /products/?select=id,name,price;product_price

# Aggregations with grouping
GET /products/?select=category,sum(price) as total&groupBy=category

# Multi-field ordering
GET /products/?orderBy=category:asc,price:desc

# Combine all features
GET /products/?category=electronics&select=name,price&orderBy=price:desc
```

### GraphQL API

```python
from basilisk import GraphQLCRUDRouter

graphql_router = GraphQLCRUDRouter(
    model=Product,
    create_schema=ProductCreate,
    response_schema=ProductResponse,
    get_db=get_db,
)

app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])
```

**GraphQL Examples:**

```graphql
# List with advanced filtering
query {
  listProducts(
    where: {
      AND: [
        { category: { eq: "electronics" } }
        { price: { gte: 100 } }
      ]
    }
    orderBy: [{ field: "price", direction: DESC }]
  ) {
    id
    name
    price
  }
}

# Relay-style pagination
query {
  productConnection(
    first: 10
    after: "cursor123"
    where: { category: { in: ["electronics", "books"] } }
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

# Create mutation
mutation {
  createProduct(input: {
    name: "Laptop"
    price: 999
    category: "electronics"
  }) {
    id
    name
    price
  }
}
```

### Multi-Model Associations (Optional)

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")

# Enable associations (opt-in)
router = CRUDRouter(
    model=User,
    create_schema=UserCreate,
    response_schema=UserResponse,
    get_db=get_db,
    enable_associations=True,  # Enable eager loading
)
```

**Usage:**

```bash
# REST: Include related data
GET /users/1?include=posts

# REST: Include nested relationships
GET /users/?include=posts.comments,profile
```

```graphql
# GraphQL: Nested queries (automatic with associations enabled)
query {
  getUser(id: 1) {
    id
    name
    posts {
      id
      title
    }
  }
}
```

### Role-Based Access Control (Optional)

```python
from basilisk import CRUDRouter, PermissionConfig
from pydantic import BaseModel

class UserContext(BaseModel):
    id: int
    roles: list[str]

# Define permissions
permissions = PermissionConfig(
    roles={
        "admin": ["create", "read", "update", "delete"],
        "user": ["read"],
        "editor": ["create", "read", "update"],
    }
)

# Your authentication dependency
def get_current_user(token: str = Header(...)) -> UserContext:
    # Your auth logic here
    return UserContext(id=1, roles=["user"])

# Apply permissions to router
router = CRUDRouter(
    model=Product,
    create_schema=ProductCreate,
    response_schema=ProductResponse,
    get_db=get_db,
    permissions=permissions,
    get_current_user=get_current_user,
)
```

**Result:** Users can only access operations allowed by their role. Unauthorized attempts return 403 Forbidden.

### MCP Mode for AI Agents (Optional)

```python
# Enable MCP mode for AI agent integration
router = CRUDRouter(
    model=Product,
    create_schema=ProductCreate,
    response_schema=ProductResponse,
    get_db=get_db,
    enable_mcp=True,  # Expose AI-friendly documentation
)
```

**MCP Endpoints:**
- `GET /products/.mcp/overview` - Complete API overview
- `GET /products/.mcp/schema` - Detailed schema information
- `GET /products/.mcp/examples` - Usage examples for all operations
- `GET /products/.mcp/capabilities` - Supported features
- `GET /products/.mcp/guide` - Best practices for agents

## Examples

See the `examples/` directory for complete working examples:

- `basic_example.py` - Simple REST API
- `graphql_example.py` - Basic GraphQL API
- `combined_example.py` - REST + GraphQL together
- `advanced_query_example.py` - Advanced filtering and aggregation
- `advanced_graphql_example.py` - GraphQL with filtering and pagination
- `rbac_example.py` - Role-based access control
- `associations_example.py` - Multi-model relationships
- `mcp_mode_example.py` - AI agent integration

## Documentation

Run any example and visit:
- REST: http://127.0.0.1:8000/docs (Swagger UI)
- GraphQL: http://127.0.0.1:8000/graphql (GraphQL Playground)

## Security

Basilisk includes built-in security features:
- **SQL Injection Prevention** - Parameterized queries via SQLAlchemy
- **Input Validation** - Column name whitelisting against model attributes
- **Sanitization** - Alphanumeric validation for aliases and function names
- **Depth Limiting** - Max nesting depth for associations (prevents circular refs)

## Requirements

- Python 3.8+
- FastAPI
- SQLAlchemy 2.0+
- Pydantic 2.0+
- Ariadne (optional, for GraphQL)

## License

MIT

## Contributing

Contributions welcome! Please check existing issues or create a new one to discuss changes.

## Roadmap

- Async database operations
- Field-level permissions
- DataLoader integration for GraphQL
- Caching strategies
- Rate limiting
- Webhooks
