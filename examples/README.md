# Basilisk Examples

This directory contains examples demonstrating how to use Basilisk to quickly create CRUD APIs.

## 📚 Available Examples

### 1. Basic Usage ([basic_usage.py](basic_usage.py))

The simplest possible example - create a full CRUD API for a User model with just a few lines of code.

**What it demonstrates:**
- Setting up a SQLAlchemy model
- Creating Pydantic schemas
- Generating CRUD routes with `CRUDRouter`
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
- How to create a minimal CRUD API in ~170 lines
- Auto-generated routes:
  - `GET /users/` - List all users with pagination
  - `GET /users/documentation` - Comprehensive API documentation
- How Basilisk integrates with FastAPI's automatic OpenAPI docs
- Database setup with SQLite
- Pydantic schema creation with field validation

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
- Advanced query filtering
- Custom endpoints alongside CRUD routes
- GraphQL integration with Ariadne
- Multiple models with relationships
- Authentication and authorization
- Async database operations

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
