"""
Comprehensive tests for the QueryParser, including security tests.

Tests cover:
- Basic filtering
- Field selection
- Ordering
- Grouping and aggregation
- SQL injection prevention
- Invalid input handling
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from basilisk.query_parser import QueryParser


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_query_parser.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Test model
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    price = Column(Integer)
    stock = Column(Integer)


# Create tables for tests
Base.metadata.create_all(bind=engine)


def setup_test_data():
    """Create test data for query parser tests."""
    db = SessionLocal()

    # Clear existing data
    db.query(Product).delete()
    db.commit()

    # Add test products
    products = [
        Product(name="Laptop", category="Electronics", price=1000, stock=10),
        Product(name="Mouse", category="Electronics", price=25, stock=100),
        Product(name="Keyboard", category="Electronics", price=75, stock=50),
        Product(name="Desk", category="Furniture", price=300, stock=20),
        Product(name="Chair", category="Furniture", price=150, stock=30),
        Product(name="Monitor", category="Electronics", price=200, stock=15),
    ]

    for product in products:
        db.add(product)

    db.commit()
    db.close()


# ============================================================================
# Basic Filtering Tests
# ============================================================================

def test_filter_single_value():
    """Test filtering with a single value."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(Product, {"category": "Electronics"})
    query = parser.build_query(db.query(Product))
    results = query.all()

    assert len(results) == 4  # 4 electronics items
    assert all(p.category == "Electronics" for p in results)

    db.close()


def test_filter_multiple_values():
    """Test filtering with comma-separated values (OR logic)."""
    setup_test_data()
    db = SessionLocal()

    # Filter: category IN ('Electronics', 'Furniture')
    parser = QueryParser(Product, {"category": "Electronics,Furniture"})
    query = parser.build_query(db.query(Product))
    results = query.all()

    assert len(results) == 6  # All products

    db.close()


def test_filter_multiple_fields():
    """Test filtering with multiple fields (AND logic)."""
    setup_test_data()
    db = SessionLocal()

    # Filter: category = 'Electronics' AND price = 25
    parser = QueryParser(Product, {"category": "Electronics", "price": "25"})
    query = parser.build_query(db.query(Product))
    results = query.all()

    assert len(results) == 1
    assert results[0].name == "Mouse"

    db.close()


def test_filter_invalid_column():
    """Test that invalid column names raise an error (SQL injection prevention)."""
    db = SessionLocal()

    # Try to filter on a non-existent column
    parser = QueryParser(Product, {"invalid_column": "value"})

    with pytest.raises(HTTPException) as exc_info:
        query = parser.build_query(db.query(Product))
        query.all()

    assert exc_info.value.status_code == 400
    assert "Invalid filter field" in exc_info.value.detail

    db.close()


# ============================================================================
# Field Selection Tests
# ============================================================================

def test_select_specific_fields():
    """Test selecting specific columns."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(Product, {"select": "id,name,price"})
    query = parser.build_query(db.query(Product))
    results = query.all()

    # Results should be tuples/named tuples with 3 fields
    assert len(results) == 6
    # Each result should have 3 elements
    assert len(results[0]) == 3

    db.close()


def test_select_with_alias():
    """Test field selection with custom aliases using semicolon syntax."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(Product, {"select": "name;product_name,price;cost"})
    query = parser.build_query(db.query(Product))
    results = query.all()

    assert len(results) == 6
    # Check that aliases are applied
    assert hasattr(results[0], "product_name") or "product_name" in results[0]._asdict()

    db.close()


def test_select_with_alias_sql_style():
    """Test field selection with SQL-style 'as' aliases."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(Product, {"select": "name as product_name,price as cost"})
    query = parser.build_query(db.query(Product))
    results = query.all()

    assert len(results) == 6
    # Check that aliases are applied
    assert hasattr(results[0], "product_name") or "product_name" in results[0]._asdict()

    db.close()


def test_select_invalid_field():
    """Test that invalid field names in select raise an error."""
    db = SessionLocal()

    parser = QueryParser(Product, {"select": "id,invalid_field"})

    with pytest.raises(HTTPException) as exc_info:
        query = parser.build_query(db.query(Product))
        query.all()

    assert exc_info.value.status_code == 400
    assert "Invalid select field" in exc_info.value.detail

    db.close()


# ============================================================================
# Ordering Tests
# ============================================================================

def test_order_by_single_field_asc():
    """Test ordering by a single field in ascending order."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(Product, {"orderBy": "price:asc"})
    query = parser.build_query(db.query(Product))
    results = query.all()

    # Check that results are ordered by price ascending
    prices = [p.price for p in results]
    assert prices == sorted(prices)
    assert results[0].name == "Mouse"  # Cheapest item

    db.close()


def test_order_by_single_field_desc():
    """Test ordering by a single field in descending order."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(Product, {"orderBy": "price:desc"})
    query = parser.build_query(db.query(Product))
    results = query.all()

    # Check that results are ordered by price descending
    prices = [p.price for p in results]
    assert prices == sorted(prices, reverse=True)
    assert results[0].name == "Laptop"  # Most expensive item

    db.close()


def test_order_by_multiple_fields():
    """Test ordering by multiple fields."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(Product, {"orderBy": "category:asc,price:desc"})
    query = parser.build_query(db.query(Product))
    results = query.all()

    # Check that results are first ordered by category, then by price desc
    assert results[0].category == "Electronics"
    assert results[-1].category == "Furniture"

    db.close()


def test_order_by_invalid_field():
    """Test that invalid field names in orderBy raise an error."""
    db = SessionLocal()

    parser = QueryParser(Product, {"orderBy": "invalid_field:asc"})

    with pytest.raises(HTTPException) as exc_info:
        query = parser.build_query(db.query(Product))
        query.all()

    assert exc_info.value.status_code == 400
    assert "Invalid order by field" in exc_info.value.detail

    db.close()


def test_order_by_invalid_direction():
    """Test that invalid order directions raise an error."""
    db = SessionLocal()

    parser = QueryParser(Product, {"orderBy": "price:invalid"})

    with pytest.raises(HTTPException) as exc_info:
        query = parser.build_query(db.query(Product))
        query.all()

    assert exc_info.value.status_code == 400
    assert "Invalid order direction" in exc_info.value.detail

    db.close()


# ============================================================================
# Grouping and Aggregation Tests
# ============================================================================

def test_group_by_with_count():
    """Test GROUP BY with COUNT aggregation using semicolon syntax."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(
        Product,
        {"select": "category,count(id);total", "groupBy": "category"}
    )
    query = parser.build_query(db.query(Product))
    results = query.all()

    # Should return 2 groups: Electronics and Furniture
    assert len(results) == 2

    # Convert to dict for easier testing
    results_dict = {row[0]: row[1] for row in results}
    assert results_dict["Electronics"] == 4
    assert results_dict["Furniture"] == 2

    db.close()


def test_group_by_with_count_sql_style():
    """Test GROUP BY with COUNT aggregation using SQL 'as' syntax."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(
        Product,
        {"select": "category,count(id) as total", "groupBy": "category"}
    )
    query = parser.build_query(db.query(Product))
    results = query.all()

    # Should return 2 groups: Electronics and Furniture
    assert len(results) == 2

    # Convert to dict for easier testing
    results_dict = {row[0]: row[1] for row in results}
    assert results_dict["Electronics"] == 4
    assert results_dict["Furniture"] == 2

    db.close()


def test_group_by_with_sum():
    """Test GROUP BY with SUM aggregation."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(
        Product,
        {"select": "category,sum(stock);total_stock", "groupBy": "category"}
    )
    query = parser.build_query(db.query(Product))
    results = query.all()

    # Should return 2 groups
    assert len(results) == 2

    # Convert to dict
    results_dict = {row[0]: row[1] for row in results}
    # Electronics: 10 + 100 + 50 + 15 = 175
    # Furniture: 20 + 30 = 50
    assert results_dict["Electronics"] == 175
    assert results_dict["Furniture"] == 50

    db.close()


def test_group_by_with_multiple_aggregations():
    """Test GROUP BY with multiple aggregation functions."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(
        Product,
        {
            "select": "category,count(id);count,sum(price);total_price,avg(price);avg_price",
            "groupBy": "category"
        }
    )
    query = parser.build_query(db.query(Product))
    results = query.all()

    assert len(results) == 2
    # Each row should have 4 fields: category, count, total_price, avg_price
    assert len(results[0]) == 4

    db.close()


def test_aggregation_invalid_function():
    """Test that invalid aggregation functions raise an error (SQL injection prevention)."""
    db = SessionLocal()

    # Try to use an invalid/dangerous function
    parser = QueryParser(
        Product,
        {"select": "drop_table(id);danger", "groupBy": "category"}
    )

    with pytest.raises(HTTPException) as exc_info:
        query = parser.build_query(db.query(Product))
        query.all()

    assert exc_info.value.status_code == 400
    assert "Invalid aggregation function" in exc_info.value.detail

    db.close()


def test_group_by_invalid_field():
    """Test that invalid field names in groupBy raise an error."""
    db = SessionLocal()

    parser = QueryParser(Product, {"groupBy": "invalid_field"})

    with pytest.raises(HTTPException) as exc_info:
        query = parser.build_query(db.query(Product))
        query.all()

    assert exc_info.value.status_code == 400
    assert "Invalid group by field" in exc_info.value.detail

    db.close()


# ============================================================================
# SQL Injection Prevention Tests
# ============================================================================

def test_sql_injection_in_filter():
    """Test that SQL injection attempts in filters are blocked."""
    db = SessionLocal()

    # Try various SQL injection patterns
    injection_attempts = [
        {"category": "'; DROP TABLE products; --"},
        {"name": "1' OR '1'='1"},
        {"price": "1; DELETE FROM products;"},
    ]

    for injection in injection_attempts:
        parser = QueryParser(Product, injection)
        query = parser.build_query(db.query(Product))

        # Query should execute safely (no SQL injection)
        # The values are treated as literals, not SQL code
        results = query.all()

        # Results should be empty (no matches) or safe
        # Most importantly, the database should not be affected
        assert isinstance(results, list)

    # Verify table still exists and has data
    count = db.query(Product).count()
    assert count == 6  # All products still there

    db.close()


def test_sql_injection_in_column_names():
    """Test that SQL injection attempts in column names are blocked."""
    db = SessionLocal()

    # Try to inject SQL through column names
    injection_attempts = [
        {"'; DROP TABLE products; --": "value"},
        {"id; DELETE FROM products": "1"},
    ]

    for injection in injection_attempts:
        parser = QueryParser(Product, injection)

        # Should raise HTTPException due to invalid column name
        with pytest.raises(HTTPException) as exc_info:
            query = parser.build_query(db.query(Product))
            query.all()

        assert exc_info.value.status_code == 400

    # Verify table still exists
    count = db.query(Product).count()
    assert count == 6

    db.close()


def test_sql_injection_in_select():
    """Test that SQL injection attempts in select are blocked."""
    setup_test_data()
    db = SessionLocal()

    # Try to inject SQL through select parameter with invalid column containing special chars
    parser = QueryParser(
        Product,
        {"select": "id OR 1=1 --"}
    )

    with pytest.raises(HTTPException) as exc_info:
        query = parser.build_query(db.query(Product))
        query.all()

    assert exc_info.value.status_code == 400
    assert "Invalid select field format" in exc_info.value.detail

    # Verify table still exists and data is intact
    count = db.query(Product).count()
    assert count == 6

    db.close()


def test_sql_injection_in_order_by():
    """Test that SQL injection attempts in orderBy are blocked."""
    db = SessionLocal()

    # Try to inject SQL through orderBy
    parser = QueryParser(
        Product,
        {"orderBy": "'; DROP TABLE products; --:asc"}
    )

    with pytest.raises(HTTPException) as exc_info:
        query = parser.build_query(db.query(Product))
        query.all()

    assert exc_info.value.status_code == 400

    db.close()


def test_sql_injection_in_aggregation():
    """Test that SQL injection attempts in aggregation functions are blocked."""
    db = SessionLocal()

    # Try to inject SQL through aggregation function name
    parser = QueryParser(
        Product,
        {"select": "system(id);hack", "groupBy": "category"}
    )

    with pytest.raises(HTTPException) as exc_info:
        query = parser.build_query(db.query(Product))
        query.all()

    assert exc_info.value.status_code == 400
    assert "Invalid aggregation function" in exc_info.value.detail

    db.close()


def test_sql_injection_in_alias():
    """Test that SQL injection attempts in aliases are blocked."""
    setup_test_data()
    db = SessionLocal()

    # Try to inject SQL through alias with special characters
    injection_attempts = [
        {"select": "name as test; DROP TABLE products"},
        {"select": "count(id) as total; DELETE FROM products"},
        {"select": "name as (SELECT * FROM products)"},
        {"select": "name;bad alias"},  # Alias with spaces
        {"select": "count(id);drop_table"},  # This should work (valid alias)
    ]

    for i, injection in enumerate(injection_attempts[:-1]):  # Skip the last valid one
        parser = QueryParser(Product, injection)

        with pytest.raises(HTTPException) as exc_info:
            query = parser.build_query(db.query(Product))
            query.all()

        assert exc_info.value.status_code == 400
        # Either field format or alias format error is acceptable
        assert ("Invalid" in exc_info.value.detail and
                ("format" in exc_info.value.detail or "field" in exc_info.value.detail))

    # Test that valid alias with underscore works
    parser = QueryParser(Product, injection_attempts[-1])
    query = parser.build_query(db.query(Product))
    results = query.all()  # Should not raise

    # Verify table still exists
    count = db.query(Product).count()
    assert count == 6

    db.close()


# ============================================================================
# Combined Query Tests
# ============================================================================

def test_combined_filter_order_select():
    """Test combining filter, order, and select."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(
        Product,
        {
            "category": "Electronics",
            "select": "name,price",
            "orderBy": "price:asc"
        }
    )
    query = parser.build_query(db.query(Product))
    results = query.all()

    assert len(results) == 4  # 4 electronics items
    # Should be ordered by price ascending
    prices = [row[1] for row in results]  # price is second field
    assert prices == sorted(prices)

    db.close()


def test_combined_all_features():
    """Test combining all query features together."""
    setup_test_data()
    db = SessionLocal()

    # Complex query: filter + group + aggregate
    # Note: ordering by aggregated aliases is not supported; order by actual columns
    parser = QueryParser(
        Product,
        {
            "select": "category,count(id);count,avg(price);avg_price",
            "groupBy": "category",
            "orderBy": "category:asc"  # Order by the grouping column
        }
    )
    query = parser.build_query(db.query(Product))
    results = query.all()

    assert len(results) == 2
    # Should be ordered by category ascending
    assert results[0][0] == "Electronics"
    assert results[1][0] == "Furniture"

    db.close()


def test_empty_query_params():
    """Test that empty query params work correctly."""
    setup_test_data()
    db = SessionLocal()

    parser = QueryParser(Product, {})
    query = parser.build_query(db.query(Product))
    results = query.all()

    # Should return all products
    assert len(results) == 6

    db.close()


# Clean up after all tests
def teardown_module():
    """Clean up test database."""
    Base.metadata.drop_all(bind=engine)
