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

### 🚧 Phase 3: Advanced Query Parsing (IN PROGRESS)
**Priority**: HIGH

Implement advanced query parsing for REST APIs with GitHub-style syntax:

#### Required Features:
1. **Filtering**:
   ```
   ?assignee=A,B,C&author=X,Y,Z
   ?status=open&priority=high,critical
   ```

2. **Field Selection**:
   ```
   ?select=col1,col2,col3
   ?select=id,name,email  # Only return specified fields
   ```

3. **Aggregation Functions**:
   ```
   ?select=col1,sum(col2),count(col3)&groupBy=col1
   ?select=sum(col1);sum_col_1,col2,count(col3);count&groupBy=col1,col3
   ```

4. **Ordering**:
   ```
   ?orderBy=name:asc,created_at:desc
   ?orderBy=[(col1,Asc),(col2,Desc)]
   ```

5. **Grouping**:
   ```
   ?groupBy=col1,col2,col3
   ```

#### Implementation Notes:
- **SECURITY**: Prevent SQL injection - validate all inputs
- Use parameterized queries via SQLAlchemy
- Consider using existing packages if they meet standards
- Flexible syntax - doesn't have to match examples exactly
- Industry standard syntax is preferred

#### Suggested Approach:
- Create `query_parser.py` module
- Parse query strings into SQLAlchemy query objects
- Support both simple and complex queries
- Add comprehensive tests for injection prevention

### 📋 Phase 4: Enhanced GraphQL (FUTURE)
- [ ] Advanced filtering in GraphQL (where clauses)
- [ ] Nested relationships
- [ ] Connection-based pagination (relay-style)
- [ ] DataLoader integration for N+1 query prevention

### 🔐 Phase 5: Authentication & Authorization (FUTURE)
- [ ] Authentication dependency helpers
- [ ] Role-based access control (RBAC)
- [ ] JWT token support
- [ ] OAuth2 integration
- [ ] Permission decorators for routes

### 🔄 Phase 6: Advanced Features (FUTURE)
- [ ] Async database support
- [ ] Multiple model relationships
- [ ] File upload handling
- [ ] Webhooks
- [ ] Rate limiting
- [ ] Caching strategies

---

## 🎯 Current Implementation Status

### What's Working:
1. ✅ REST API with basic list endpoint
2. ✅ GraphQL API with full CRUD
3. ✅ Automatic schema generation (both REST and GraphQL)
4. ✅ Documentation endpoint for REST
5. ✅ Working examples for REST, GraphQL, and combined
6. ✅ Pydantic model integration
7. ✅ SQLAlchemy 2.0 support
8. ✅ FastAPI integration
9. ✅ Interactive docs (Swagger for REST, Playground for GraphQL)

### What's NOT Implemented Yet:
1. ❌ REST: Create, Update, Delete operations
2. ❌ Advanced query parsing (filtering, groupBy, orderBy, etc.)
3. ❌ Field selection in REST
4. ❌ Aggregation functions
5. ❌ Authentication/Authorization
6. ❌ Relationship handling
7. ❌ Async database operations

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

1. **Implement full REST CRUD operations** (create, get, update, delete)
2. **Add query parser for advanced filtering**
3. **Add comprehensive tests for query parser**
4. **Add field selection support**
5. **Add aggregation functions**
6. **Security audit for SQL injection prevention**
7. **Add authentication framework**
8. **Add relationship support**

---

**Last Updated**: 2025-10-11
**Current Version**: 0.1.0
**Status**: Active Development
