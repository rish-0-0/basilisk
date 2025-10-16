# Basilisk Examples

This directory contains examples demonstrating how to use Basilisk to quickly create CRUD APIs.

## 📚 Available Examples

### 1. Basic Usage - REST API ([basic_usage.py](basic_usage.py))

The simplest possible example - create a full REST CRUD API for a User model with just a few lines of code.

**What it demonstrates:**
- Setting up a SQLAlchemy model
- Creating Pydantic schemas
- Generating REST CRUD routes with `CRUDRouter`
- Accessing the auto-generated documentation endpoint

**Run it:**
```bash
python examples/basic_usage.py
```

**Try it out:**
- Interactive Swagger docs: http://localhost:8000/docs
- API documentation: http://localhost:8000/users/documentation
- List users: http://localhost:8000/users/

---

### 2. GraphQL Usage ([graphql_usage.py](graphql_usage.py))

Create a full GraphQL API with queries and mutations using `GraphQLCRUDRouter`.

**What it demonstrates:**
- Auto-generating GraphQL schema from Pydantic models
- GraphQL queries (list, get single item)
- GraphQL mutations (create, update, delete)
- Interactive GraphQL Playground
- Advanced query parameters (orderBy, skip, limit)

**Run it:**
```bash
python examples/graphql_usage.py
```

**Try it out:**
- GraphQL Playground: http://localhost:8000/graphql/
- View schema: http://localhost:8000/schema

**Example queries:**
```graphql
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

# Update a user
mutation {
  updateUser(id: 1, input: { name: "Alice Johnson" }) {
    id
    name
  }
}
```

---

## 🚀 Quick Start

1. **Install Basilisk with dev dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Run any example:**
   ```bash
   python examples/basic_usage.py
   ```

3. **Open your browser:**
   - Go to http://localhost:8000/docs
   - Try out the API endpoints interactively!

---

## 🎯 What You'll Learn

### From `basic_usage.py`:
- How to create a minimal REST CRUD API in ~170 lines
- Auto-generated routes:
  - `GET /users/` - List all users with pagination
  - `GET /users/documentation` - Comprehensive API documentation
- How Basilisk integrates with FastAPI's automatic OpenAPI docs
- Database setup with SQLite
- Pydantic schema creation with field validation

### From `graphql_usage.py`:
- Auto-generating GraphQL schemas from Pydantic models
- GraphQL queries with filtering and pagination
- GraphQL mutations (create, update, delete)
- Using Ariadne for GraphQL integration
- Interactive GraphQL Playground

---

## 🔄 Using Both REST and GraphQL Together

You can easily use both REST and GraphQL in the same application:

```python
from basilisk import CRUDRouter, GraphQLCRUDRouter

# REST API
rest_router = CRUDRouter(
    model=User,
    create_schema=UserCreate,
    response_schema=UserResponse,
    get_db=get_db,
    prefix="/api/users",
)
app.include_router(rest_router.router)

# GraphQL API
graphql_router = GraphQLCRUDRouter(
    model=User,
    create_schema=UserCreate,
    update_schema=UserUpdate,
    response_schema=UserResponse,
    get_db=get_db,
)
app.mount("/graphql", graphql_router.app)
```

This gives you:
- REST endpoints at `/api/users/`
- GraphQL endpoint at `/graphql/`
- REST Swagger docs at `/docs`
- GraphQL Playground at `/graphql/`

---

## 📖 Understanding the Documentation Endpoint

Each CRUD router automatically gets a `/documentation` endpoint that provides:

```json
{
  "resource": "User",
  "table_name": "users",
  "endpoints": {
    "list": { /* endpoint details */ },
    "get": { /* endpoint details */ },
    "create": { /* endpoint details */ },
    // ... more endpoints
  },
  "schemas": {
    "create": { /* schema fields */ },
    "response": { /* schema fields */ }
  },
  "database_model": {
    "columns": { /* column information */ }
  }
}
```

**Try it:**
```bash
curl http://localhost:8000/users/documentation | python -m json.tool
```

---

## 🧪 Testing the Examples

You can test any example using `curl` or `httpx`:

```bash
# List users (empty initially)
curl http://localhost:8000/users/

# Get documentation
curl http://localhost:8000/users/documentation

# Health check
curl http://localhost:8000/health
```

---

## 🔮 Coming Soon

More examples will be added demonstrating:
- Advanced query filtering (GitHub-style query syntax)
- Custom endpoints alongside CRUD routes
- Multiple models with relationships
- Authentication and authorization
- Async database operations
- Using both REST and GraphQL together in one app

---

## 💡 Tips

1. **Check the database:** Each example creates a SQLite database file (e.g., `example_users.db`). You can inspect it with any SQLite browser.

2. **Enable SQL logging:** Set `echo=True` in `create_engine()` to see all SQL queries.

3. **Interactive docs:** FastAPI's `/docs` endpoint is the best way to explore and test the API.

4. **Documentation endpoint:** Use `/users/documentation` (or `/{prefix}/documentation`) to get machine-readable API metadata - perfect for generating client SDKs or documentation.

---

## 🐛 Troubleshooting

**Port already in use?**
```bash
# Change the port in the example file
uvicorn.run(app, host="0.0.0.0", port=8001)  # Use 8001 instead
```

**Database locked?**
```bash
# Remove the database file and restart
rm example_users.db
python examples/basic_usage.py
```

**Import errors?**
```bash
# Make sure you've installed basilisk in development mode
pip install -e ".[dev]"
```
