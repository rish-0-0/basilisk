"""
GraphQL router generator for CRUD operations using Ariadne.

This module provides a GraphQL router that works alongside or instead of
the REST router, giving developers flexibility in API design.
"""

from typing import Any, Callable

from ariadne import MutationType, QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .graphql_schema import generate_graphql_schema


class GraphQLCRUDRouter:
    """
    Generates GraphQL router with CRUD operations.

    Provides queries and mutations for a SQLAlchemy model using Ariadne.

    Example:
        graphql_router = GraphQLCRUDRouter(
            model=User,
            create_schema=UserCreate,
            update_schema=UserUpdate,
            response_schema=UserResponse,
            get_db=get_db,
            path="/graphql",
        )

        app.mount("/graphql", graphql_router.app)
    """

    def __init__(
        self,
        *,
        model: type[Any],
        create_schema: type[BaseModel],
        response_schema: type[BaseModel],
        update_schema: type[BaseModel] | None = None,
        get_db: Callable,
        path: str = "/graphql",
        resource_name: str | None = None,
    ):
        """
        Initialize the GraphQL CRUD router.

        Args:
            model: SQLAlchemy model class
            create_schema: Pydantic schema for creating records
            response_schema: Pydantic schema for responses
            update_schema: Optional Pydantic schema for updates
            get_db: Database session dependency
            path: GraphQL endpoint path
            resource_name: Name of the resource (defaults to model.__name__)
        """
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.get_db = get_db
        self.path = path
        self.resource_name = resource_name or model.__name__

        # Generate schema
        self.schema_str = generate_graphql_schema(
            response_model=response_schema,
            create_model=create_schema,
            update_model=update_schema,
            resource_name=self.resource_name,
        )

        # Setup resolvers
        self.query = QueryType()
        self.mutation = MutationType()
        self._setup_query_resolvers()
        self._setup_mutation_resolvers()

        # Create executable schema
        self.executable_schema = make_executable_schema(
            self.schema_str, self.query, self.mutation
        )

        # Create GraphQL app with context
        self.app = GraphQL(
            self.executable_schema,
            context_value=self._get_context,
            debug=True,
        )

    def _get_context(self, request: Any) -> dict[str, Any]:
        """Get context for GraphQL resolvers (includes DB session)."""
        db = next(self.get_db())
        return {"db": db, "request": request}

    def _setup_query_resolvers(self) -> None:
        """Setup query resolvers for list and get operations."""
        resource_lower = self.resource_name.lower()
        resource_plural = f"{resource_lower}s"

        # Resolver for getting a single item
        @self.query.field(resource_lower)
        def resolve_get(obj: Any, info: Any, id: int) -> dict[str, Any] | None:
            """Get a single record by ID."""
            db: Session = info.context["db"]
            item = db.query(self.model).filter(self.model.id == id).first()

            if not item:
                return None

            # Convert SQLAlchemy model to dict
            return self._model_to_dict(item)

        # Resolver for listing items
        @self.query.field(resource_plural)
        def resolve_list(
            obj: Any,
            info: Any,
            skip: int = 0,
            limit: int = 100,
            orderBy: list[str] | None = None,
            where: dict[str, Any] | None = None,
        ) -> list[dict[str, Any]]:
            """
            List records with filtering and pagination.

            Args:
                skip: Number of records to skip
                limit: Maximum number of records to return
                orderBy: List of columns to order by (e.g., ["name", "id:desc"])
                where: Filter conditions (supports comparison operators and logical operators)
            """
            db: Session = info.context["db"]
            query = db.query(self.model)

            # Apply WHERE filtering
            if where:
                query = self._apply_where_filters(query, where)

            # Apply ordering
            if orderBy:
                for order_field in orderBy:
                    if ":" in order_field:
                        field, direction = order_field.split(":")
                        if hasattr(self.model, field):
                            col = getattr(self.model, field)
                            if direction.lower() == "desc":
                                query = query.order_by(col.desc())
                            else:
                                query = query.order_by(col.asc())
                    else:
                        if hasattr(self.model, order_field):
                            query = query.order_by(getattr(self.model, order_field))

            # Apply pagination
            items = query.offset(skip).limit(limit).all()

            # Convert to dicts
            return [self._model_to_dict(item) for item in items]

    def _setup_mutation_resolvers(self) -> None:
        """Setup mutation resolvers for create, update, and delete operations."""
        resource_name = self.resource_name

        # Create mutation
        @self.mutation.field(f"create{resource_name}")
        def resolve_create(obj: Any, info: Any, input: dict[str, Any]) -> dict[str, Any]:
            """Create a new record."""
            db: Session = info.context["db"]

            # Validate with Pydantic
            validated_data = self.create_schema(**input)

            # Create SQLAlchemy model instance
            db_obj = self.model(**validated_data.model_dump())
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)

            return self._model_to_dict(db_obj)

        # Update mutation (if update schema provided)
        if self.update_schema:

            @self.mutation.field(f"update{resource_name}")
            def resolve_update(
                obj: Any, info: Any, id: int, input: dict[str, Any]
            ) -> dict[str, Any] | None:
                """Update an existing record."""
                db: Session = info.context["db"]

                # Get existing record
                db_obj = db.query(self.model).filter(self.model.id == id).first()
                if not db_obj:
                    return None

                # Validate with Pydantic
                validated_data = self.update_schema(**input)

                # Update fields
                for field, value in validated_data.model_dump(exclude_unset=True).items():
                    if hasattr(db_obj, field):
                        setattr(db_obj, field, value)

                db.commit()
                db.refresh(db_obj)

                return self._model_to_dict(db_obj)

        # Delete mutation
        @self.mutation.field(f"delete{resource_name}")
        def resolve_delete(obj: Any, info: Any, id: int) -> bool:
            """Delete a record."""
            db: Session = info.context["db"]

            db_obj = db.query(self.model).filter(self.model.id == id).first()
            if not db_obj:
                return False

            db.delete(db_obj)
            db.commit()
            return True

    def _apply_where_filters(self, query: Any, where_dict: dict[str, Any]) -> Any:
        """
        Apply WHERE filters to a SQLAlchemy query.

        Supports:
        - Equality: {field: value}
        - IN clause: {field_in: [value1, value2]}
        - NOT: {field_not: value}
        - Comparisons: {field_lt/lte/gt/gte: value}
        - Logical operators: {AND: [...], OR: [...], NOT: {...}}

        Args:
            query: SQLAlchemy query object
            where_dict: Dictionary of filter conditions

        Returns:
            Modified query with filters applied
        """
        from sqlalchemy import and_, or_, not_

        for key, value in where_dict.items():
            # Handle logical operators
            if key == "AND":
                if isinstance(value, list):
                    conditions = [
                        self._build_filter_condition(cond) for cond in value
                    ]
                    query = query.filter(and_(*conditions))
            elif key == "OR":
                if isinstance(value, list):
                    conditions = [
                        self._build_filter_condition(cond) for cond in value
                    ]
                    query = query.filter(or_(*conditions))
            elif key == "NOT":
                if isinstance(value, dict):
                    condition = self._build_filter_condition(value)
                    query = query.filter(not_(condition))
            else:
                # Handle field-level filters
                query = self._apply_field_filter(query, key, value)

        return query

    def _build_filter_condition(self, where_dict: dict[str, Any]) -> Any:
        """Build a filter condition from a where dictionary."""
        from sqlalchemy import and_

        conditions = []
        for key, value in where_dict.items():
            if key in ["AND", "OR", "NOT"]:
                continue  # These will be handled by _apply_where_filters
            condition = self._get_field_condition(key, value)
            if condition is not None:
                conditions.append(condition)

        if len(conditions) == 1:
            return conditions[0]
        return and_(*conditions)

    def _get_field_condition(self, key: str, value: Any) -> Any | None:
        """Get SQLAlchemy condition for a field filter."""
        # Parse field name and operator
        if "_in" in key:
            field_name = key.replace("_in", "")
            if hasattr(self.model, field_name):
                column = getattr(self.model, field_name)
                return column.in_(value)
        elif "_not" in key:
            field_name = key.replace("_not", "")
            if hasattr(self.model, field_name):
                column = getattr(self.model, field_name)
                return column != value
        elif "_lt" in key:
            field_name = key.replace("_lt", "")
            if hasattr(self.model, field_name):
                column = getattr(self.model, field_name)
                return column < value
        elif "_lte" in key:
            field_name = key.replace("_lte", "")
            if hasattr(self.model, field_name):
                column = getattr(self.model, field_name)
                return column <= value
        elif "_gt" in key:
            field_name = key.replace("_gt", "")
            if hasattr(self.model, field_name):
                column = getattr(self.model, field_name)
                return column > value
        elif "_gte" in key:
            field_name = key.replace("_gte", "")
            if hasattr(self.model, field_name):
                column = getattr(self.model, field_name)
                return column >= value
        else:
            # Simple equality
            if hasattr(self.model, key):
                column = getattr(self.model, key)
                return column == value

        return None

    def _apply_field_filter(self, query: Any, key: str, value: Any) -> Any:
        """Apply a single field filter to the query."""
        condition = self._get_field_condition(key, value)
        if condition is not None:
            query = query.filter(condition)
        return query

    def _model_to_dict(self, model_instance: Any) -> dict[str, Any]:
        """Convert SQLAlchemy model instance to dictionary."""
        return {
            c.name: getattr(model_instance, c.name)
            for c in model_instance.__table__.columns
        }
