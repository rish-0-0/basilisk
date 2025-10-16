"""
Query parser module for advanced filtering, field selection, ordering, and aggregation.

This module provides secure query parsing for REST API endpoints, supporting:
- Filtering with multiple values per field
- Field selection (SELECT specific columns)
- Ordering (ORDER BY with ASC/DESC)
- Grouping and aggregation functions
- SQL injection prevention through validation

Example usage:
    parser = QueryParser(
        model=User,
        query_params={"name": "John,Jane", "age": "25", "select": "id,name,email"}
    )
    query = parser.build_query(db.query(User))
    results = query.all()
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, asc, desc
from sqlalchemy.orm import Query
from fastapi import HTTPException


class QueryParser:
    """
    Parse URL query parameters into SQLAlchemy queries.

    Supports:
    - Filtering: ?status=active&role=admin,user
    - Selection: ?select=id,name,email
    - Aliases: ?select=name;product_name or ?select=name as product_name
    - Ordering: ?orderBy=name:asc,created_at:desc
    - Grouping: ?groupBy=status,role
    - Aggregation: ?select=count(id);total or ?select=count(id) as total

    Security Features:
    - Validates all column names against model attributes
    - Prevents SQL injection through whitelist validation
    - Uses parameterized queries via SQLAlchemy
    - Validates aggregation function names
    """

    # Allowed aggregation functions (whitelist for security)
    ALLOWED_AGGREGATIONS = {
        "count",
        "sum",
        "avg",
        "min",
        "max",
    }

    # Allowed order directions
    ALLOWED_ORDER_DIRECTIONS = {"asc", "desc"}

    def __init__(self, model: type[Any], query_params: Dict[str, str]):
        """
        Initialize the query parser.

        Args:
            model: SQLAlchemy model class
            query_params: Dictionary of query parameters from the request

        Example:
            parser = QueryParser(User, {"name": "John", "age": "25"})
        """
        self.model = model
        self.params = dict(query_params)  # Convert to dict for easier handling

        # Extract special parameters
        self.select_fields = self._extract_param("select")
        self.order_by = self._extract_param("orderBy")
        self.group_by = self._extract_param("groupBy")

        # Reserved parameter names (not used for filtering)
        self.reserved_params = {"select", "orderBy", "groupBy", "skip", "limit"}

    def _extract_param(self, param_name: str) -> Optional[str]:
        """Extract and remove a parameter from the params dict."""
        return self.params.pop(param_name, None)

    def _validate_column_name(self, column_name: str) -> bool:
        """
        Validate that a column name exists in the model.

        Args:
            column_name: Name of the column to validate

        Returns:
            True if valid, False otherwise

        Security:
            This prevents SQL injection by ensuring only valid model
            attributes can be referenced in queries.
        """
        return hasattr(self.model, column_name)

    def _parse_filter_values(self, value: str) -> List[str]:
        """
        Parse comma-separated filter values.

        Args:
            value: Comma-separated string (e.g., "admin,user,guest")

        Returns:
            List of individual values

        Example:
            >>> self._parse_filter_values("admin,user")
            ["admin", "user"]
        """
        return [v.strip() for v in value.split(",") if v.strip()]

    def apply_filters(self, query: Query) -> Query:
        """
        Apply WHERE filters to the query.

        Supports multiple values per field using OR logic:
        - ?status=active,pending → WHERE status IN ('active', 'pending')

        Args:
            query: Base SQLAlchemy query

        Returns:
            Query with filters applied

        Raises:
            HTTPException: If invalid column name is provided

        Example:
            >>> query = db.query(User)
            >>> query = parser.apply_filters(query)
        """
        for field_name, value in self.params.items():
            # Skip reserved parameters
            if field_name in self.reserved_params:
                continue

            # Validate column name (security check)
            if not self._validate_column_name(field_name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid filter field: {field_name}. "
                    f"Field does not exist in {self.model.__name__} model.",
                )

            # Parse comma-separated values
            values = self._parse_filter_values(value)

            if not values:
                continue

            # Get the model attribute
            column = getattr(self.model, field_name)

            # Apply filter with IN clause for multiple values, equality for single value
            if len(values) == 1:
                query = query.filter(column == values[0])
            else:
                query = query.filter(column.in_(values))

        return query

    def _parse_select_fields(self) -> List[Tuple[Any, Optional[str]]]:
        """
        Parse field selection with optional aggregation functions.

        Supports:
        - Simple fields: "id,name,email"
        - Aggregations: "count(id);total,status"
        - Mixed: "status,count(id);user_count"

        Returns:
            List of tuples (column_expression, alias)

        Raises:
            HTTPException: If invalid field or function name

        Example:
            >>> parser.select_fields = "count(id);total,name"
            >>> parser._parse_select_fields()
            [(func.count(User.id), "total"), (User.name, None)]
        """
        if not self.select_fields:
            return []

        fields = []
        for field_spec in self.select_fields.split(","):
            field_spec = field_spec.strip()
            if not field_spec:
                continue

            # Check for aggregation function: count(id);alias, count(id) as alias, or count(id)
            if "(" in field_spec:
                # Parse: function_name(column_name);alias, function_name(column_name) as alias, or function_name(column_name)

                # Handle both semicolon and 'as' syntax for aliases
                if ";" in field_spec:
                    parts = field_spec.split(";")
                    func_part = parts[0].strip()
                    alias = parts[1].strip() if len(parts) > 1 else None
                elif " as " in field_spec.lower():
                    # Support SQL-style: count(id) as total
                    parts = field_spec.lower().split(" as ")
                    func_part = parts[0].strip()
                    alias = parts[1].strip() if len(parts) > 1 else None
                else:
                    func_part = field_spec.strip()
                    alias = None

                # Validate alias if present (security check - must be alphanumeric + underscore)
                if alias and (not alias or not alias.replace("_", "").isalnum()):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid alias format: {alias}. Aliases must be alphanumeric with underscores only.",
                    )

                # Extract function name and column
                func_name = func_part[: func_part.index("(")].strip().lower()
                column_name = func_part[func_part.index("(") + 1 : func_part.rindex(")")].strip()

                # Validate function name (security check)
                if func_name not in self.ALLOWED_AGGREGATIONS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid aggregation function: {func_name}. "
                        f"Allowed: {', '.join(self.ALLOWED_AGGREGATIONS)}",
                    )

                # Validate column name (security check)
                if not self._validate_column_name(column_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid column in aggregation: {column_name}",
                    )

                # Build aggregation expression
                column = getattr(self.model, column_name)
                agg_func = getattr(func, func_name)
                fields.append((agg_func(column), alias))

            else:
                # Simple field selection (no aggregation)
                # Support both semicolon and 'as' syntax: field;alias or field as alias
                if ";" in field_spec:
                    parts = field_spec.split(";")
                    field_name = parts[0].strip()
                    alias = parts[1].strip() if len(parts) > 1 else None
                elif " as " in field_spec.lower():
                    # Support SQL-style: name as product_name
                    parts = field_spec.lower().split(" as ")
                    field_name = parts[0].strip()
                    alias = parts[1].strip() if len(parts) > 1 else None
                else:
                    field_name = field_spec.strip()
                    alias = None

                # Validate that we have a valid field name (not SQL injection)
                # Field name should be alphanumeric + underscore only (no spaces or special chars)
                if not field_name or not field_name.replace("_", "").isalnum():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid select field format: {field_name}",
                    )

                # Validate alias if present (security check)
                if alias and (not alias or not alias.replace("_", "").isalnum()):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid alias format: {alias}. Aliases must be alphanumeric with underscores only.",
                    )

                # Validate column name (security check)
                if not self._validate_column_name(field_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid select field: {field_name}",
                    )

                column = getattr(self.model, field_name)
                fields.append((column, alias))

        return fields

    def apply_selection(self, query: Query) -> Query:
        """
        Apply column selection to query.

        If select_fields is provided, only those columns are returned.
        Otherwise, all columns are returned (default behavior).

        Args:
            query: Base SQLAlchemy query

        Returns:
            Query with column selection applied

        Example:
            >>> parser.select_fields = "id,name,email"
            >>> query = parser.apply_selection(query)
        """
        if not self.select_fields:
            return query

        fields = self._parse_select_fields()
        if not fields:
            return query

        # Build column list with labels (aliases)
        columns = []
        for column_expr, alias in fields:
            if alias:
                columns.append(column_expr.label(alias))
            else:
                columns.append(column_expr)

        # Replace the query with selected columns
        # Note: This returns tuples/named tuples, not model instances
        return query.with_entities(*columns)

    def _parse_order_by(self) -> List[Tuple[str, str]]:
        """
        Parse order by specification.

        Supports:
        - Single field: "name:asc"
        - Multiple fields: "name:asc,created_at:desc"
        - Default direction: "name" (defaults to asc)

        Returns:
            List of tuples (column_name, direction)

        Example:
            >>> parser.order_by = "name:asc,age:desc"
            >>> parser._parse_order_by()
            [("name", "asc"), ("age", "desc")]
        """
        if not self.order_by:
            return []

        order_specs = []
        for spec in self.order_by.split(","):
            spec = spec.strip()
            if not spec:
                continue

            # Parse "column:direction" or just "column" (default to asc)
            if ":" in spec:
                column_name, direction = spec.split(":", 1)
                column_name = column_name.strip()
                direction = direction.strip().lower()
            else:
                column_name = spec
                direction = "asc"

            order_specs.append((column_name, direction))

        return order_specs

    def apply_ordering(self, query: Query) -> Query:
        """
        Apply ORDER BY to query.

        Args:
            query: Base SQLAlchemy query

        Returns:
            Query with ordering applied

        Raises:
            HTTPException: If invalid column or direction

        Example:
            >>> parser.order_by = "name:asc,created_at:desc"
            >>> query = parser.apply_ordering(query)
        """
        order_specs = self._parse_order_by()

        for column_name, direction in order_specs:
            # Validate column name (security check)
            if not self._validate_column_name(column_name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid order by field: {column_name}",
                )

            # Validate direction (security check)
            if direction not in self.ALLOWED_ORDER_DIRECTIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid order direction: {direction}. "
                    f"Allowed: {', '.join(self.ALLOWED_ORDER_DIRECTIONS)}",
                )

            # Get the column
            column = getattr(self.model, column_name)

            # Apply ordering
            if direction == "asc":
                query = query.order_by(asc(column))
            else:
                query = query.order_by(desc(column))

        return query

    def _parse_group_by(self) -> List[str]:
        """
        Parse group by specification.

        Supports:
        - Single field: "status"
        - Multiple fields: "status,role"

        Returns:
            List of column names

        Example:
            >>> parser.group_by = "status,role"
            >>> parser._parse_group_by()
            ["status", "role"]
        """
        if not self.group_by:
            return []

        return [field.strip() for field in self.group_by.split(",") if field.strip()]

    def apply_grouping(self, query: Query) -> Query:
        """
        Apply GROUP BY to query.

        Note: Grouping is typically used with aggregation functions
        in the SELECT clause.

        Args:
            query: Base SQLAlchemy query

        Returns:
            Query with grouping applied

        Raises:
            HTTPException: If invalid column name

        Example:
            >>> parser.group_by = "status,role"
            >>> query = parser.apply_grouping(query)
        """
        group_fields = self._parse_group_by()

        for field_name in group_fields:
            # Validate column name (security check)
            if not self._validate_column_name(field_name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid group by field: {field_name}",
                )

            # Get the column
            column = getattr(self.model, field_name)

            # Apply grouping
            query = query.group_by(column)

        return query

    def build_query(self, base_query: Query) -> Query:
        """
        Build complete query from parameters.

        Applies all query modifications in the correct order:
        1. Filters (WHERE)
        2. Grouping (GROUP BY)
        3. Selection (SELECT) - must come after GROUP BY
        4. Ordering (ORDER BY)

        Note: Pagination (LIMIT/OFFSET) should be applied after this
        method by the router.

        Args:
            base_query: Base SQLAlchemy query (typically db.query(Model))

        Returns:
            Fully constructed query ready for execution

        Example:
            >>> parser = QueryParser(User, request.query_params)
            >>> query = parser.build_query(db.query(User))
            >>> results = query.all()
        """
        query = base_query

        # Apply filters first
        query = self.apply_filters(query)

        # Apply grouping before selection (required for aggregations)
        query = self.apply_grouping(query)

        # Apply selection (this can change the query return type)
        query = self.apply_selection(query)

        # Apply ordering last
        query = self.apply_ordering(query)

        return query
