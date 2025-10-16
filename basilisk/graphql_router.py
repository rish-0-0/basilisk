"""
GraphQL router generator for CRUD operations using Ariadne.

This module provides a GraphQL router that works alongside or instead of
the REST router, giving developers flexibility in API design.
"""

from typing import Any, Callable, Optional

from ariadne import MutationType, QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .graphql_schema import generate_graphql_schema

try:
    from .permissions import PermissionChecker, PermissionConfig, UserContext
    PERMISSIONS_AVAILABLE = True
except ImportError:
    PERMISSIONS_AVAILABLE = False
    PermissionChecker = None  # type: ignore
    PermissionConfig = None  # type: ignore
    UserContext = None  # type: ignore


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
        permissions: Optional[Any] = None,  # PermissionConfig type
        get_current_user: Optional[Callable] = None,
        enable_associations: bool = False,
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
            permissions: Optional PermissionConfig for RBAC
            get_current_user: Optional dependency for getting current user
            enable_associations: Enable relationship/association support (opt-in)
        """
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.get_db = get_db
        self.path = path
        self.resource_name = resource_name or model.__name__
        self.get_current_user = get_current_user

        # Setup permissions if provided
        self.permission_checker = None
        if permissions and PERMISSIONS_AVAILABLE:
            self.permission_checker = PermissionChecker(
                config=permissions,
                get_current_user=get_current_user,
            )

        # Setup associations if enabled (check if module is available)
        try:
            from .associations import get_model_associations
            self.enable_associations = enable_associations
            self._associations_module_available = True
        except ImportError:
            self.enable_associations = False
            self._associations_module_available = False

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
        """
        Get context for GraphQL resolvers (includes DB session and user).

        Returns:
            Context dictionary with db, request, and optionally user
        """
        db = next(self.get_db())
        context = {"db": db, "request": request, "user": None}

        # Get current user if authentication is configured
        if self.get_current_user:
            try:
                user = self.get_current_user(request)
                context["user"] = user
            except Exception:
                # If authentication fails, leave user as None
                pass

        return context

    def _check_permission(self, operation: str, user: Any) -> None:
        """
        Check if user has permission for an operation.

        Args:
            operation: Operation name (read, create, update, delete)
            user: User context from GraphQL context

        Raises:
            Exception: If permission is denied
        """
        if self.permission_checker:
            if not self.permission_checker.config.is_allowed(operation, user):
                raise Exception(f"Permission denied: {operation} operation requires appropriate role")

    def _setup_query_resolvers(self) -> None:
        """Setup query resolvers for list and get operations."""
        resource_lower = self.resource_name.lower()
        resource_plural = f"{resource_lower}s"

        # Resolver for getting a single item
        @self.query.field(resource_lower)
        def resolve_get(obj: Any, info: Any, id: int) -> dict[str, Any] | None:
            """Get a single record by ID."""
            # Check permission
            user = info.context.get("user")
            self._check_permission("read", user)

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
            # Check permission
            user = info.context.get("user")
            self._check_permission("read", user)

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

        # Resolver for Relay-style connection pagination
        @self.query.field(f"{resource_plural}Connection")
        def resolve_connection(
            obj: Any,
            info: Any,
            first: int | None = None,
            after: str | None = None,
            last: int | None = None,
            before: str | None = None,
            orderBy: list[str] | None = None,
            where: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            """
            List records with Relay-style cursor pagination.

            Args:
                first: Number of items to return from the start
                after: Cursor to start after
                last: Number of items to return from the end
                before: Cursor to end before
                orderBy: List of columns to order by
                where: Filter conditions
            """
            # Check permission
            user = info.context.get("user")
            self._check_permission("read", user)

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

            # Get total count for the query
            total_count = query.count()

            # Handle cursor-based pagination
            if after:
                after_id = self._decode_cursor(after)
                query = query.filter(self.model.id > after_id)

            if before:
                before_id = self._decode_cursor(before)
                query = query.filter(self.model.id < before_id)

            # Apply limits
            if first:
                query = query.limit(first + 1)  # +1 to check if there's a next page
            elif last:
                # For last, we need to reverse the query
                query = query.order_by(self.model.id.desc()).limit(last + 1)

            items = query.all()

            # Determine if there are more pages
            has_next_page = False
            has_previous_page = False

            if first and len(items) > first:
                has_next_page = True
                items = items[:first]

            if last and len(items) > last:
                has_previous_page = True
                items = items[:last]
                items = list(reversed(items))  # Reverse back to correct order

            # Build edges
            edges = []
            for item in items:
                edges.append({
                    "node": self._model_to_dict(item),
                    "cursor": self._encode_cursor(item.id)
                })

            # Build page info
            page_info = {
                "hasNextPage": has_next_page,
                "hasPreviousPage": has_previous_page,
                "startCursor": edges[0]["cursor"] if edges else None,
                "endCursor": edges[-1]["cursor"] if edges else None,
            }

            return {
                "edges": edges,
                "pageInfo": page_info,
                "totalCount": total_count,
            }

    def _setup_mutation_resolvers(self) -> None:
        """Setup mutation resolvers for create, update, and delete operations."""
        resource_name = self.resource_name

        # Create mutation
        @self.mutation.field(f"create{resource_name}")
        def resolve_create(obj: Any, info: Any, input: dict[str, Any]) -> dict[str, Any]:
            """Create a new record."""
            # Check permission
            user = info.context.get("user")
            self._check_permission("create", user)

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
                # Check permission
                user = info.context.get("user")
                self._check_permission("update", user)

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
            # Check permission
            user = info.context.get("user")
            self._check_permission("delete", user)

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
        """
        Convert SQLAlchemy model instance to dictionary.

        If associations are enabled, includes related objects as nested dictionaries.
        """
        result = {
            c.name: getattr(model_instance, c.name)
            for c in model_instance.__table__.columns
        }

        # Include associations if enabled
        if self.enable_associations and self._associations_module_available:
            from .associations import get_model_associations

            associations = get_model_associations(type(model_instance))

            for assoc_name, assoc_info in associations.items():
                # Check if the association is loaded (to avoid lazy loading issues)
                if hasattr(model_instance, assoc_name):
                    related_obj = getattr(model_instance, assoc_name)

                    if related_obj is not None:
                        if assoc_info.uselist:
                            # One-to-many or many-to-many: return list of dicts
                            result[assoc_name] = [
                                self._model_to_dict(item) for item in related_obj
                            ]
                        else:
                            # One-to-one or many-to-one: return single dict
                            result[assoc_name] = self._model_to_dict(related_obj)
                    else:
                        result[assoc_name] = None if not assoc_info.uselist else []

        return result

    def _encode_cursor(self, id_value: int) -> str:
        """
        Encode an ID into a cursor string (base64).

        Args:
            id_value: The ID value to encode

        Returns:
            Base64-encoded cursor string
        """
        import base64
        cursor_str = f"cursor:{id_value}"
        return base64.b64encode(cursor_str.encode()).decode()

    def _decode_cursor(self, cursor: str) -> int:
        """
        Decode a cursor string back into an ID.

        Args:
            cursor: Base64-encoded cursor string

        Returns:
            The decoded ID value

        Raises:
            ValueError: If cursor is invalid
        """
        import base64
        try:
            decoded = base64.b64decode(cursor.encode()).decode()
            if decoded.startswith("cursor:"):
                return int(decoded.split(":", 1)[1])
            raise ValueError("Invalid cursor format")
        except Exception as e:
            raise ValueError(f"Invalid cursor: {e}") from e
