# Basilisk Development Guide

This document contains the coding standards, milestones, and implementation notes for the Basilisk package. Use this as a reference when working on the project.

---

## 🎯 Project Vision

**Basilisk** is a FastAPI package that auto-generates CRUD routes from Pydantic models for both REST and GraphQL APIs. It's designed for rapid application scaffolding while maintaining code quality and modularity.

**Core Principle**: Pass in a Pydantic model → get fully functional CRUD routes

---

## 📏 Coding Standards

### 1. Code Maintainability is PARAMOUNT

> ⚠️ **CRITICAL**: Code maintainability cannot be sacrificed for more features. Always prioritize clean, maintainable code over adding new features.

- Write **extremely well documented code**
- Use proper, readable directory structure
- **Be willing to backtrack and refactor** if structure doesn't support maintainability
- Use **dependency injection pattern** extensively
- Keep files **modular and well-named** for easy imports

### 2. Documentation Requirements

- Every module must have a comprehensive docstring
- Every class must explain its purpose and usage with examples
- Every public function must document:
  - Purpose
  - Arguments (with types)
  - Return values
  - Usage examples where applicable
- Include inline comments for complex logic

### 3. Module Organization

Keep imports granular and specific:
```python
# Good - allows importing specific components
from basilisk import CRUDRouter
from basilisk.query_parser import QueryParser
from basilisk.graphql_schema import generate_graphql_schema

# Not just:
from basilisk import *
```

### 4. File Naming Conventions

Files should be named for their specific purpose:
- `router.py` - REST router generation
- `graphql_router.py` - GraphQL router generation
- `graphql_schema.py` - GraphQL schema generation
- `query_parser.py` - Query string parsing (future)
- `auth.py` - Authentication dependencies (future)

This allows developers to import only what they need.

### 5. Dependency Injection

Use FastAPI's dependency injection throughout:
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pass as dependency, don't instantiate directly
router = CRUDRouter(..., get_db=get_db)
```

---

## 🗺️ Implementation Roadmap

### ✅ Phase 1: Foundation (COMPLETED)
- [x] Project structure setup
- [x] Basic REST CRUD router
- [x] TDD with first test
- [x] Examples folder with working example
- [x] Documentation endpoint for REST

### ✅ Phase 2: GraphQL Support (COMPLETED)
- [x] GraphQL schema generation from Pydantic models
- [x] GraphQL CRUD router with Ariadne
- [x] Queries: list, get single item
- [x] Mutations: create, update, delete
- [x] GraphQL example
- [x] Combined REST + GraphQL example

### ✅ Phase 3: Advanced Query Parsing (COMPLETED)

Implemented advanced query parsing for REST APIs with industry-standard syntax.

#### Implemented Features:
1. **Filtering**:
   - Multiple values per field: `?status=active,pending`
   - Multiple filters: `?status=active&role=admin,user`
   - OR logic within fields, AND logic across fields

2. **Field Selection**:
   - Simple fields: `?select=id,name,email`
   - With aliases: `?select=name;product_name` or `?select=name as product_name`

3. **Aggregation Functions**:
   - Count, sum, avg, min, max supported
   - With grouping: `?select=category,count(id) as total&groupBy=category`
   - With aliases: `?select=sum(amount);total_amount&groupBy=status`

4. **Ordering**:
   - Single field: `?orderBy=name:asc`
   - Multiple fields: `?orderBy=name:asc,created_at:desc`
   - Default direction (asc): `?orderBy=name`

5. **Grouping**:
   - Single field: `?groupBy=status`
   - Multiple fields: `?groupBy=status,role`

#### Security Features:
- ✅ SQL injection prevention through whitelist validation
- ✅ Column name validation against model attributes
- ✅ Parameterized queries via SQLAlchemy
- ✅ Aggregation function name validation
- ✅ Alphanumeric validation for aliases

### ✅ Phase 4: Enhanced GraphQL (COMPLETED)

Enhanced GraphQL API with advanced querying capabilities to match REST feature parity.

#### Implemented Features:
1. **Advanced Filtering in GraphQL**:
   - ✅ `where` clauses with field-level filters
   - ✅ Comparison operators: `eq`, `in`, `not`, `lt`, `lte`, `gt`, `gte`
   - ✅ Logical operators: `AND`, `OR`, `NOT`
   - ✅ Nested filter conditions
   - ✅ Works with both list and connection queries

2. **Connection-Based Pagination** (Relay-style):
   - ✅ Cursor-based pagination using base64-encoded IDs
   - ✅ Support for `first`, `after`, `last`, `before` arguments
   - ✅ Returns `edges` with `node` and `cursor`
   - ✅ `pageInfo` with `hasNextPage`, `hasPreviousPage`, `startCursor`, `endCursor`
   - ✅ `totalCount` for total results
   - ✅ More scalable than offset-based pagination
   - ✅ Works with ordering and filtering

3. **Enhanced Ordering**:
   - ✅ Multi-field ordering support
   - ✅ Direction specification (asc/desc)
   - ✅ Works with both list and connection queries

#### What's Not Implemented (Future):
- ❌ Nested relationships in queries (Phase 6)
- ❌ DataLoader integration for N+1 prevention (Phase 6)
- ❌ Field-level permissions in GraphQL
- ❌ Subscription support

#### Examples:
- See `examples/advanced_graphql_example.py` for comprehensive examples
- Demonstrates all Phase 4 features with real use cases

### ✅ Phase 5: Role-Based Access Control (COMPLETED)

Implemented RBAC system for controlling access to CRUD operations based on user roles.

**Note**: This phase focuses ONLY on authorization (RBAC). Authentication (JWT, OAuth2, etc.) is handled by the user's application.

#### Implemented Features:
1. **Role Definition System**:
   - ✅ `PermissionConfig` class for defining role-based permissions
   - ✅ Dictionary mapping roles to allowed operations (create, read, update, delete)
   - ✅ Flexible configuration per resource
   - ✅ Support for anonymous access to specific operations

2. **Permission Checking**:
   - ✅ `PermissionChecker` class for validating permissions
   - ✅ Automatic integration with FastAPI dependencies
   - ✅ User context extraction from requests
   - ✅ Clear permission denied errors (HTTP 403)

3. **CRUDRouter Integration**:
   - ✅ Optional `permissions` parameter in CRUDRouter
   - ✅ Optional `get_current_user` dependency injection
   - ✅ Automatic protection of all CRUD endpoints
   - ✅ Operation-level permissions (list, get, create, update, delete)

4. **GraphQL Integration**:
   - ✅ Permission checks in all GraphQL resolvers
   - ✅ Query permissions (read operations)
   - ✅ Mutation permissions (create, update, delete operations)
   - ✅ Consistent authorization across REST and GraphQL
   - ✅ User context passed through GraphQL context

5. **Resource-Level Permissions**:
   - ✅ `ResourcePermissionChecker` for custom permission logic
   - ✅ Support for permission callback functions
   - ✅ Custom checks in `PermissionConfig`
   - ✅ Example: "users can only edit their own posts"

6. **User Context**:
   - ✅ `UserContext` base model with id and roles
   - ✅ Extensible for custom user models
   - ✅ Integration with any authentication system

#### Examples:
- See `examples/rbac_example.py` for comprehensive RBAC implementation
- Demonstrates REST and GraphQL with multiple roles
- Shows custom permission functions for resource-level access

#### What's Not Implemented (Future):
- ❌ Field-level permissions (hiding specific fields based on role)
- ❌ Built-in JWT/OAuth2 authentication (user provides this)
- ❌ Permission caching/optimization
- ❌ Audit logging for permission checks

### ✅ Phase 6: Multi-Model Associations (COMPLETED)
**Priority**: MEDIUM

Implemented support for SQLAlchemy relationships (associations) in both REST and GraphQL APIs as an **OPT-IN** feature.

#### Implemented Features:
1. **One-to-Many Relationships**:
   - Parent can have multiple children
   - Automatic nested queries
   - Example: User has many Posts
     ```python
     class User(Base):
         __tablename__ = "users"
         id = Column(Integer, primary_key=True)
         posts = relationship("Post", back_populates="author")

     class Post(Base):
         __tablename__ = "posts"
         id = Column(Integer, primary_key=True)
         author_id = Column(Integer, ForeignKey("users.id"))
         author = relationship("User", back_populates="posts")
     ```

2. **Many-to-One Relationships**:
   - Child belongs to parent
   - Query child with parent data
   - Example: Post belongs to User
   - Inverse of one-to-many

3. **One-to-One Relationships**:
   - Single record relates to single record
   - Example: User has one Profile
     ```python
     class User(Base):
         __tablename__ = "users"
         id = Column(Integer, primary_key=True)
         profile = relationship("Profile", back_populates="user", uselist=False)

     class Profile(Base):
         __tablename__ = "profiles"
         id = Column(Integer, primary_key=True)
         user_id = Column(Integer, ForeignKey("users.id"), unique=True)
         user = relationship("User", back_populates="profile")
     ```

4. **Many-to-Many Relationships**:
   - Records relate through association table
   - Example: Users have many Roles, Roles have many Users
     ```python
     user_roles = Table('user_roles', Base.metadata,
         Column('user_id', Integer, ForeignKey('users.id')),
         Column('role_id', Integer, ForeignKey('roles.id'))
     )

     class User(Base):
         __tablename__ = "users"
         id = Column(Integer, primary_key=True)
         roles = relationship("Role", secondary=user_roles, back_populates="users")

     class Role(Base):
         __tablename__ = "roles"
         id = Column(Integer, primary_key=True)
         users = relationship("User", secondary=user_roles, back_populates="roles")
     ```

#### REST API Support:
1. **Nested Resource Routes**:
   - `/users/{user_id}/posts` - List posts for a user
   - `/users/{user_id}/posts/{post_id}` - Get specific post
   - Support CRUD on nested resources

2. **Include Related Data**:
   - Query parameter to include relationships: `?include=posts,profile`
   - Eager loading to prevent N+1 queries
   - Control depth of nesting: `?include=posts.comments`

3. **Filtering by Relationships**:
   - Filter by related model fields: `?author.name=John`
   - Support joins in query parser

#### GraphQL API Support:
1. **Nested Queries**:
   - Automatic resolvers for relationships
   - Query related data in single request
     ```graphql
     query {
       getUser(id: 1) {
         id
         name
         posts {
           id
           title
         }
         profile {
           bio
         }
       }
     }
     ```

2. **Relationship Mutations**:
   - Create related records together
   - Associate/dissociate relationships
   - Update through relationships

3. **DataLoader Integration**:
   - Batch relationship queries
   - Prevent N+1 query problem
   - Cache related data per request

#### Implementation Notes:
- ✅ **OPT-IN Design**: Associations are completely optional via `enable_associations=True`
- ✅ **Auto-detection**: Automatically detects all SQLAlchemy relationship types
- ✅ **Eager Loading**: Implements `joinedload` to prevent N+1 query problems
- ✅ **Security**: Validates relationship names and limits nesting depth (max 3 levels)
- ✅ **Circular Reference Protection**: Max depth parameter prevents infinite loops
- ✅ **REST API**: `?include=posts,profile` or `?include=posts.tags,profile`
- ✅ **GraphQL API**: Automatic nested resolvers when associations enabled
- ✅ **Comprehensive Tests**: 18 tests covering all functionality
- ✅ **Example**: `examples/associations_example.py` demonstrates all 4 relationship types

#### Usage:
```python
# REST API with associations
router = CRUDRouter(
    model=User,
    create_schema=UserCreate,
    response_schema=UserResponse,
    get_db=get_db,
    enable_associations=True,  # OPT-IN
)

# Query with includes
# GET /users/?include=posts,profile
# GET /posts/?include=author,tags
# GET /users/1?include=posts.tags,profile

# GraphQL with associations
graphql_router = GraphQLCRUDRouter(
    model=User,
    create_schema=UserCreate,
    response_schema=UserResponse,
    get_db=get_db,
    enable_associations=True,  # OPT-IN
)
```

#### Files Created:
- `basilisk/associations.py` - Core association utilities module (optional)
- `examples/associations_example.py` - Comprehensive example with all relationship types
- `tests/test_associations.py` - Full test suite for associations

---

## 🎯 Current Implementation Status

### What's Working:
1. ✅ **REST API with full CRUD**:
   - GET (list with pagination)
   - GET by ID (single record)
   - POST (create)
   - PUT (update)
   - DELETE
   - Optional: Include parameter for eager loading associations
2. ✅ **GraphQL API with full CRUD**:
   - Queries: list, get single item
   - Mutations: create, update, delete
   - Optional: Nested relationship resolvers
3. ✅ **Advanced Query Parsing**:
   - Filtering with multiple values per field
   - Field selection with aliases
   - Aggregation functions (count, sum, avg, min, max)
   - Ordering (ASC/DESC)
   - Grouping
   - SQL injection prevention
4. ✅ **GraphQL Enhancements**:
   - Relay-style connection pagination with cursors
   - Advanced WHERE filtering (eq, in, not, lt, lte, gt, gte)
   - Logical operators (AND, OR, NOT)
   - Multi-field ordering
5. ✅ **Role-Based Access Control (RBAC)** - Optional:
   - Permission system with role configuration
   - Operation-level permissions
   - Resource-level custom checks
   - Integration with both REST and GraphQL
   - User context management
6. ✅ **Multi-Model Associations** - Optional:
   - One-to-Many relationships
   - Many-to-One relationships
   - One-to-One relationships
   - Many-to-Many relationships
   - Eager loading with ?include parameter
   - Nested relationship support
   - Automatic GraphQL nested resolvers
   - Security: validation and depth limiting
7. ✅ **Automatic Schema Generation**:
   - REST schemas from Pydantic models
   - GraphQL schemas from Pydantic models with WHERE inputs
   - Relay connection types
8. ✅ **Documentation**:
   - REST documentation endpoint
   - Interactive Swagger UI
   - GraphQL Playground
9. ✅ **Core Features**:
   - Pydantic model integration
   - SQLAlchemy 2.0 support
   - FastAPI integration
   - Proper error handling
   - Security features (SQL injection prevention, input validation)
   - Optional dependencies (Ariadne for GraphQL)
   - Optional features (RBAC, Associations)

### What's NOT Implemented Yet:
1. ❌ **Future Enhancements**:
   - Async database operations
   - File upload handling
   - Webhooks
   - Rate limiting
   - Caching strategies
   - DataLoader integration for GraphQL (advanced N+1 prevention)
   - Field-level permissions in GraphQL

---

## 🚨 Important Notes & Gotchas

### 1. Testing Database
- Use **SQLite** for all examples and tests
- File-based SQLite (not `:memory:`) to avoid threading issues on Windows
- Add all test databases to `.gitignore`

### 2. Pagination
- Use simple **limit/offset** pagination for now
- Default: `skip=0`, `limit=100`
- Max limit: `1000` to prevent abuse

### 3. GraphQL Context
- Pass database session through GraphQL context
- Handle session lifecycle properly (open/close)
- Each request gets its own session

### 4. Windows Compatibility
- Use `127.0.0.1` instead of `0.0.0.0` for better Windows support
- Handle UTF-8 encoding for console output with emojis
- Use forward slashes or `Path` for cross-platform paths

### 5. Optional Dependencies
- Ariadne (GraphQL) is optional
- Package should work without GraphQL if Ariadne not installed
- Use try/except in `__init__.py` for graceful degradation

### 6. Security Considerations (CRITICAL)
- **Never** allow raw SQL in query parameters
- Always use SQLAlchemy's parameterized queries
- Validate all user inputs against model schema
- Sanitize column names against model attributes
- Use `hasattr(model, column)` checks before accessing attributes

### 7. Schema Generation
- Auto-generate from Pydantic models, not SQLAlchemy directly
- Keep schemas separate from models for flexibility
- Support both create and update schemas (different validation)
- Response schema should have `from_attributes=True` for ORM conversion

---

## 📚 Code Examples for Future Features

### Query Parser (to be implemented)

```python
# basilisk/query_parser.py

class QueryParser:
    """
    Parse URL query parameters into SQLAlchemy queries.

    Supports:
    - Filtering: ?status=active&role=admin,user
    - Selection: ?select=id,name,email
    - Ordering: ?orderBy=name:asc,created_at:desc
    - Grouping: ?groupBy=status,role
    - Aggregation: ?select=count(id);total&groupBy=status
    """

    def __init__(self, model, query_params):
        self.model = model
        self.params = query_params

    def apply_filters(self, query):
        """Apply WHERE filters to query."""
        # Implementation: parse params, validate, apply filters
        pass

    def apply_selection(self, query):
        """Apply column selection to query."""
        # Implementation: validate columns exist, apply select
        pass

    def apply_ordering(self, query):
        """Apply ORDER BY to query."""
        # Implementation: parse orderBy, validate columns
        pass

    def build_query(self, base_query):
        """Build complete query from parameters."""
        query = base_query
        query = self.apply_filters(query)
        query = self.apply_selection(query)
        query = self.apply_ordering(query)
        return query
```

### Usage in Router

```python
# In router.py, future implementation:

@router.get("/")
def list_items(
    request: Request,
    db: Session = Depends(get_db)
):
    base_query = db.query(self.model)

    # Parse and apply query parameters
    parser = QueryParser(self.model, request.query_params)
    query = parser.build_query(base_query)

    items = query.all()
    return items
```

---

## 🧪 Testing Strategy

### Test Requirements:
1. **TDD Approach**: Write tests before implementing features
2. **Coverage**: Aim for >80% code coverage
3. **Test Types**:
   - Unit tests for individual functions
   - Integration tests for router endpoints
   - Security tests for SQL injection prevention

### Test Structure:
```
tests/
├── test_router.py           # REST router tests
├── test_graphql_router.py   # GraphQL router tests
├── test_query_parser.py     # Query parsing tests (future)
├── test_security.py         # Security tests (future)
└── fixtures.py              # Shared test fixtures
```

---

## 🎨 Design Principles

1. **Convention over Configuration**: Sensible defaults, but configurable
2. **Explicit over Implicit**: Clear, readable code
3. **Modular**: Each component can be used independently
4. **Extensible**: Easy to add custom logic
5. **Type Safe**: Use type hints everywhere
6. **DRY**: Don't repeat yourself
7. **YAGNI**: You ain't gonna need it - implement features when needed

---

## 📦 Package Distribution

- Package name: `basilisk`
- PyPI ready structure
- Semantic versioning: `0.1.0` (currently)
- MIT License
- Dependencies kept minimal (FastAPI, SQLAlchemy, Pydantic core only)
- Optional dependencies: `ariadne` for GraphQL

---

## 🔧 Development Workflow

1. **Before implementing a feature**:
   - Write tests first (TDD)
   - Update this document if needed
   - Check for existing packages/standards

2. **While implementing**:
   - Write comprehensive docstrings
   - Add inline comments for complex logic
   - Keep functions small and focused
   - Use type hints

3. **After implementing**:
   - Verify all tests pass
   - Update examples if needed
   - Update README
   - Check code maintainability

4. **Before committing**:
   - Run tests: `pytest`
   - Check types: `mypy` (future)
   - Format code: `black` (future)
   - Lint: `ruff` (future)

---

## 📖 Resources & References

- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/
- Pydantic: https://docs.pydantic.dev/
- Ariadne: https://ariadnegraphql.org/
- GraphQL: https://graphql.org/

---

## 🎯 Next Steps (Priority Order)

### Phase 4: Enhanced GraphQL (High Priority)
1. **Implement advanced filtering in GraphQL**
   - Where clauses with comparison operators
   - AND/OR logic
   - Field-level filters
2. **Add nested relationships to GraphQL**
   - Detect SQLAlchemy relationships
   - Auto-generate resolvers
   - DataLoader integration for N+1 prevention
3. **Implement connection-based pagination**
   - Relay-style cursors
   - PageInfo with hasNext/hasPrevious
   - Edges and nodes structure
4. **Add comprehensive tests for GraphQL enhancements**

### Phase 5: RBAC (Medium Priority)
1. **Design RBAC system architecture**
   - Role definition system
   - Permission decorators
   - Integration with FastAPI dependencies
2. **Implement permission decorators**
   - Route-level permissions
   - Resource-level permissions
   - Custom permission functions
3. **Add RBAC to both REST and GraphQL**
   - Consistent authorization across APIs
   - Clear error messages
4. **Document integration with auth libraries**
   - Examples with common auth packages
   - Best practices guide

### Phase 6: Multi-Model Relationships (Medium Priority)
1. **Implement one-to-many relationships**
   - Auto-detect from SQLAlchemy
   - REST nested routes
   - GraphQL nested queries
2. **Implement many-to-one relationships**
   - Inverse of one-to-many
   - Include related data in queries
3. **Implement one-to-one relationships**
   - Profile pattern support
   - Unique constraints
4. **Implement many-to-many relationships**
   - Association table support
   - Bi-directional queries
5. **Add relationship filtering**
   - Filter by related model fields
   - Join support in query parser
6. **Comprehensive examples and tests**
   - Multi-model examples
   - Performance testing
   - N+1 query prevention

---

**Last Updated**: 2025-10-16
**Current Version**: 0.3.0
**Status**: Active Development - Phases 1-6 Complete (REST, GraphQL, Query Parsing, RBAC, Associations)
