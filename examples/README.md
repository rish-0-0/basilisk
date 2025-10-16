# Basilisk Examples

This directory contains comprehensive examples demonstrating all features of Basilisk across all completed phases.

## 📚 Available Examples

### 1. Basic Usage - REST API ([basic_usage.py](basic_usage.py))
**Phase 1: Foundation**

The simplest possible example - create a full REST CRUD API for a User model with just a few lines of code.

**What it demonstrates:**
- Setting up a SQLAlchemy model
- Creating Pydantic schemas
- Generating REST CRUD routes with `CRUDRouter`
- Accessing the auto-generated documentation endpoint
- Basic pagination (skip, limit)

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
**Phase 2: GraphQL Support**

Create a full GraphQL API with queries and mutations using `GraphQLCRUDRouter`.

**What it demonstrates:**
- Auto-generating GraphQL schema from Pydantic models
- GraphQL queries (list, get single item)
- GraphQL mutations (create, update, delete)
- Interactive GraphQL Playground
- Basic query parameters (orderBy, skip, limit)

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
```

---

### 3. Combined REST and GraphQL ([combined_rest_and_graphql.py](combined_rest_and_graphql.py))
**Phase 2: GraphQL Support**

Demonstrates using BOTH REST and GraphQL APIs together in the same FastAPI application.

**What it demonstrates:**
- Running REST and GraphQL side-by-side
- Shared database and models
- Different API styles for different use cases
- Flexibility of Basilisk

**Run it:**
```bash
python examples/combined_rest_and_graphql.py
```

**Try it out:**
- REST API: http://localhost:8000/api/users/
- GraphQL API: http://localhost:8000/graphql/
- Swagger docs: http://localhost:8000/docs

---

### 4. Advanced Query Parsing ([advanced_query_parsing_example.py](advanced_query_parsing_example.py))
**Phase 3: Advanced Query Parsing**

Comprehensive demonstration of advanced REST API query features with industry-standard syntax.

**What it demonstrates:**
- **Filtering**: Multiple values per field with OR logic
  - `?status=active,pending`
  - `?category=Electronics&status=active,inactive`
- **Field Selection**: Choose specific fields
  - `?select=id,name,price`
- **Aliases**: Rename fields in output
  - `?select=name;product_name,price;cost`
- **Aggregation**: count, sum, avg, min, max
  - `?select=category,count(id);total&groupBy=category`
  - `?select=category,avg(price);avg_price&groupBy=category`
- **Ordering**: Single or multiple fields
  - `?orderBy=price:desc`
  - `?orderBy=category:asc,price:desc`
- **Grouping**: Group by one or more fields
  - `?groupBy=category`
  - `?groupBy=category,status`
- **Security**: SQL injection prevention, column validation

**Run it:**
```bash
python examples/advanced_query_parsing_example.py
```

**Try it out:**
- API Docs: http://localhost:8000/docs
- Root endpoint with examples: http://localhost:8000/
- Seed test data: POST http://localhost:8000/seed

**Example queries:**
```bash
# Filter by multiple values
GET /products/?category=Electronics,Books&status=active

# Select specific fields with aliases
GET /products/?select=name;product_name,price;cost

# Aggregation with grouping
GET /products/?select=category,count(id);total&groupBy=category

# Complex query
GET /products/?category=Electronics&select=name,price&orderBy=price:desc&limit=10
```

---

### 5. Advanced GraphQL ([advanced_graphql_example.py](advanced_graphql_example.py))
**Phase 4: Enhanced GraphQL**

Demonstrates advanced GraphQL features including Relay-style pagination and complex filtering.

**What it demonstrates:**
- **Connection-Based Pagination** (Relay-style)
  - Cursor-based pagination with edges and nodes
  - `pageInfo` with hasNextPage, hasPreviousPage, startCursor, endCursor
  - `first`, `after`, `last`, `before` arguments
- **Advanced Filtering**
  - WHERE clauses with comparison operators
  - `eq`, `in`, `not`, `lt`, `lte`, `gt`, `gte`
  - Logical operators: AND, OR, NOT
  - Nested filter conditions
- **Multi-field Ordering**
  - Order by multiple fields with asc/desc

**Run it:**
```bash
python examples/advanced_graphql_example.py
```

**Try it out:**
- GraphQL Playground: http://localhost:8000/graphql
- Root endpoint with examples: http://localhost:8000/
- Seed test data: POST http://localhost:8000/seed

**Example queries:**
```graphql
# Relay-style connection pagination
query {
  productsConnection(first: 10, after: "cursor") {
    edges {
      node { id name price }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}

# Advanced filtering with WHERE
query {
  products(where: {
    price_gte: 50
    price_lte: 200
    category: "Electronics"
  }) {
    id name price category
  }
}

# Logical operators (AND, OR)
query {
  products(where: {
    AND: [
      { price_gte: 50 },
      { OR: [
        { category: "Electronics" },
        { category: "Books" }
      ]}
    ]
  }) {
    id name category price
  }
}
```

---

### 6. Role-Based Access Control ([rbac_example.py](rbac_example.py))
**Phase 5: RBAC (Optional)**

Comprehensive RBAC system demonstrating authorization for both REST and GraphQL APIs.

**What it demonstrates:**
- **Role Definition**: Configure permissions per role
- **Permission Checking**: Automatic validation on all endpoints
- **Operation-Level Permissions**: create, read, update, delete
- **Resource-Level Permissions**: Custom permission functions
- **User Context**: Integration with authentication systems
- **Anonymous Access**: Allow public access to specific operations
- **REST & GraphQL**: Consistent authorization across both APIs

**Run it:**
```bash
python examples/rbac_example.py
```

**Try it out:**
- REST API: http://localhost:8000/posts
- GraphQL: http://localhost:8000/graphql
- API Docs: http://localhost:8000/docs
- Seed test data: POST http://localhost:8000/seed

**Available test tokens:**
- `admin_token` - Full access (CRUD)
- `editor_token` - Read and Update
- `author_token` - Create and Read
- `viewer_token` - Read only

**Example requests:**
```bash
# REST with authentication
curl -H "Authorization: Bearer admin_token" http://localhost:8000/posts

# GraphQL with authentication
curl -H "Authorization: Bearer admin_token" \
  -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ posts { id title } }"}'
```

---

### 7. Multi-Model Associations ([associations_example.py](associations_example.py))
**Phase 6: Associations (Optional)**

Comprehensive example demonstrating all four SQLAlchemy relationship types with opt-in support.

**What it demonstrates:**
- **One-to-Many**: User has many Posts
- **Many-to-One**: Post belongs to User (author)
- **One-to-One**: User has one Profile
- **Many-to-Many**: Post has many Tags, Tag has many Posts
- **REST API**: `?include` parameter for eager loading
  - `?include=posts,profile`
  - `?include=author,tags`
  - `?include=posts.tags,profile` (nested)
- **GraphQL API**: Automatic nested resolvers
- **Security**: Relationship validation and depth limiting
- **Opt-In Design**: Enable with `enable_associations=True`

**Run it:**
```bash
python examples/associations_example.py
```

**Try it out:**
- REST Docs: http://localhost:8000/docs
- GraphQL (Users): http://localhost:8000/graphql/users
- GraphQL (Posts): http://localhost:8000/graphql/posts
- Seed test data: POST http://localhost:8000/seed

**Example REST queries:**
```bash
# Include related data
GET /users/?include=posts,profile
GET /posts/?include=author,tags
GET /users/1?include=posts.tags,profile

# Standard queries without associations
GET /users/
GET /posts/
```

**Example GraphQL queries:**
```graphql
# Nested relationships
query {
  getUser(id: 1) {
    id
    name
    posts {
      id
      title
      tags {
        name
      }
    }
    profile {
      bio
      website
    }
  }
}
```

---

### 8. MCP Mode for AI Agents ([mcp_mode_example.py](mcp_mode_example.py))
**Phase 7: MCP Mode (Optional)**

Demonstrates MCP (Model Context Protocol) mode, which provides specialized endpoints for AI agents to understand and interact with your API.

**What it demonstrates:**
- **AI Agent Integration**: Endpoints designed for machine consumption
- **/.mcp/overview**: Complete API overview in single response
- **/.mcp/schema**: Detailed Pydantic and SQLAlchemy schema information
- **/.mcp/examples**: Comprehensive usage examples for all endpoints
- **/.mcp/capabilities**: List of supported operations and features
- **/.mcp/guide**: Best practices guide for AI agents
- **Machine-Readable**: JSON format optimized for AI understanding
- **Context-Aware**: Reflects actual API configuration (associations, permissions, etc.)
- **Opt-In Design**: Enable with `enable_mcp=True`

**Run it:**
```bash
python examples/mcp_mode_example.py
```

**Try it out:**
- Overview: http://localhost:8000/products/.mcp/overview
- Schema: http://localhost:8000/products/.mcp/schema
- Examples: http://localhost:8000/products/.mcp/examples
- Capabilities: http://localhost:8000/products/.mcp/capabilities
- Guide: http://localhost:8000/products/.mcp/guide
- Standard API: http://localhost:8000/products/
- Seed data: POST http://localhost:8000/seed

**Use Cases:**
- AI assistants helping users interact with your API
- Automated API testing and validation
- API discovery and exploration
- Documentation generation
- Client SDK generation
- Bot integration without manual prompting

**Example MCP Response:**
```json
{
  "resource": "Product",
  "model": {
    "name": "Product",
    "columns": { "id": {...}, "name": {...}, ...},
    "associations": {...}
  },
  "schemas": {
    "create": {...},
    "update": {...},
    "response": {...}
  },
  "endpoints": {
    "list": {"method": "GET", "path": "/", "supports": [...]},
    ...
  },
  "features": {
    "associations": false,
    "permissions": false,
    "advanced_querying": true,
    "pagination": true
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

## 🎯 Feature Matrix

| Feature | Example | Phase |
|---------|---------|-------|
| Basic REST CRUD | `basic_usage.py` | 1 |
| Basic GraphQL | `graphql_usage.py` | 2 |
| Combined APIs | `combined_rest_and_graphql.py` | 2 |
| Filtering (REST) | `advanced_query_parsing_example.py` | 3 |
| Field Selection | `advanced_query_parsing_example.py` | 3 |
| Aggregation | `advanced_query_parsing_example.py` | 3 |
| Ordering | `advanced_query_parsing_example.py` | 3 |
| Grouping | `advanced_query_parsing_example.py` | 3 |
| Relay Pagination | `advanced_graphql_example.py` | 4 |
| GraphQL Filtering | `advanced_graphql_example.py` | 4 |
| RBAC | `rbac_example.py` | 5 |
| Associations | `associations_example.py` | 6 |
| MCP Mode | `mcp_mode_example.py` | 7 |

---

## 📖 Learning Path

### Beginner
1. Start with `basic_usage.py` - Learn the fundamentals
2. Try `graphql_usage.py` - Understand GraphQL basics
3. Explore `combined_rest_and_graphql.py` - See how they work together

### Intermediate
4. Study `advanced_query_parsing_example.py` - Master REST queries
5. Explore `advanced_graphql_example.py` - Advanced GraphQL features
6. Review `rbac_example.py` - Add authorization

### Advanced
7. Dive into `associations_example.py` - Multi-model relationships
8. Explore `mcp_mode_example.py` - AI agent integration

---

## 🧪 Testing the Examples

You can test any example using `curl`, `httpx`, or the interactive docs:

### REST API Testing
```bash
# List items (empty initially)
curl http://localhost:8000/users/

# Get documentation
curl http://localhost:8000/users/documentation

# Health check
curl http://localhost:8000/health
```

### GraphQL Testing
Visit the GraphQL Playground in your browser or use curl:
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ users { id name } }"}'
```

---

## 💡 Tips

1. **Check the database:** Each example creates a SQLite database file (e.g., `example_users.db`). You can inspect it with any SQLite browser.

2. **Enable SQL logging:** Set `echo=True` in `create_engine()` to see all SQL queries.

3. **Interactive docs:** FastAPI's `/docs` endpoint is the best way to explore and test the API.

4. **Documentation endpoint:** Use `/{prefix}/documentation` to get machine-readable API metadata - perfect for generating client SDKs.

5. **Seed data:** Most examples have a `/seed` endpoint to populate test data. Always seed before testing!

6. **Port conflicts:** If port 8000 is in use, change it in the example file.

---

## 🔒 Security Examples

All examples demonstrate security best practices:
- **SQL Injection Prevention**: Whitelist validation, parameterized queries
- **Input Validation**: Pydantic schemas with constraints
- **Authentication**: RBAC example shows integration patterns
- **Authorization**: Permission checks at operation and resource levels

---

## 🐛 Troubleshooting

**Port already in use?**
```bash
# Change the port in the example file
uvicorn.run(app, host="127.0.0.1", port=8001)  # Use 8001 instead
```

**Database locked?**
```bash
# Remove the database file and restart
rm example_*.db
python examples/basic_usage.py
```

**Import errors?**
```bash
# Make sure you've installed basilisk in development mode
pip install -e ".[dev]"
```

**GraphQL not working?**
```bash
# Install optional GraphQL dependencies
pip install ariadne
```

---

## 🎓 Understanding the Examples

### REST vs GraphQL

**When to use REST** (`basic_usage.py`, `advanced_query_parsing_example.py`):
- Simple CRUD operations
- Caching is important
- Standard HTTP semantics
- Query parameters for filtering

**When to use GraphQL** (`graphql_usage.py`, `advanced_graphql_example.py`):
- Complex nested queries
- Client needs flexibility
- Reduce over-fetching
- Real-time subscriptions (future)

**Use Both** (`combined_rest_and_graphql.py`):
- Support different clients
- Gradual migration
- Best of both worlds

---

## 📚 Additional Resources

- **CLAUDE.md**: Detailed implementation notes and architecture
- **README.md**: Package overview and installation
- **Basilisk Docs**: Full API reference (coming soon)
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **GraphQL Docs**: https://graphql.org/

---

## 🔮 What's Next?

Basilisk is under active development. Future enhancements include:
- Async database operations
- File upload handling
- Webhooks
- Rate limiting
- Caching strategies
- DataLoader integration for GraphQL
- Field-level permissions

Check `CLAUDE.md` for the full roadmap!

---

**Last Updated**: 2025-10-16
**Version**: 0.3.0
**Status**: All Phases 1-7 Complete (REST, GraphQL, Query Parsing, GraphQL Enhancements, RBAC, Associations, MCP Mode)
