"""FastAPI router generator for CRUD operations."""

from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from .query_parser import QueryParser


class CRUDRouter:
    """
    Generates FastAPI router with CRUD endpoints.

    Minimal implementation for TDD - generates a basic list endpoint.

    Example:
        router = CRUDRouter(
            model=User,
            create_schema=UserCreate,
            response_schema=UserResponse,
            get_db=get_db,
            prefix="/users",
        )

        app.include_router(router.router)
    """

    def __init__(
        self,
        *,
        model: type[Any],
        create_schema: type[BaseModel],
        response_schema: type[BaseModel],
        get_db: Callable,
        prefix: str = "",
        tags: list[str] | None = None,
        update_schema: type[BaseModel] | None = None,
    ):
        """Initialize the CRUD router."""
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema or create_schema  # Use create_schema if update_schema not provided
        self.response_schema = response_schema
        self.get_db = get_db

        # Create the FastAPI router
        self.router = APIRouter(prefix=prefix, tags=tags or [model.__name__])  # type: ignore[arg-type]

        # Add routes (pass schemas to avoid mypy issues with decorators)
        self._add_list_route(self.response_schema, self.model, self.get_db)
        self._add_get_route(self.response_schema, self.model, self.get_db)
        self._add_create_route(self.create_schema, self.response_schema, self.model, self.get_db)
        self._add_update_route(self.update_schema, self.response_schema, self.model, self.get_db)
        self._add_delete_route(self.model, self.get_db)
        self._add_documentation_route()

    def _add_list_route(self, response_schema: type[BaseModel], model: type[Any], get_db: Callable) -> None:
        """Add GET / route for listing records with advanced query support."""

        @self.router.get("/", response_model=list[response_schema])  # type: ignore[valid-type]
        def list_items(
            request: Request,
            skip: int = Query(0, ge=0, description="Number of records to skip"),
            limit: int = Query(
                100, ge=1, le=1000, description="Maximum number of records to return"
            ),
            db: Session = Depends(get_db),
        ):
            """
            List all records with pagination and advanced query features.

            Supports:
            - Filtering: ?field=value or ?field=value1,value2 (OR logic)
            - Field selection: ?select=field1,field2 or ?select=field1 as alias1,field2
            - Ordering: ?orderBy=field1:asc,field2:desc
            - Grouping: ?groupBy=field1,field2
            - Aggregation: ?select=count(id) as total&groupBy=status

            Examples:
            - ?status=active&role=admin,user
            - ?select=id,name,email&orderBy=name:asc
            - ?select=category,count(id) as total&groupBy=category
            """
            # Create base query
            base_query = db.query(model)

            # Parse and apply advanced query parameters (filtering, grouping, selection, ordering)
            parser = QueryParser(model, dict(request.query_params))
            query = parser.build_query(base_query)

            # Apply pagination (skip/limit)
            query = query.offset(skip).limit(limit)

            # Execute query
            items = query.all()
            return items

    def _add_get_route(self, response_schema: type[BaseModel], model: type[Any], get_db: Callable) -> None:
        """Add GET /{id} route for retrieving a single record."""

        @self.router.get("/{item_id}", response_model=response_schema)
        def get_item(
            item_id: int,
            db: Session = Depends(get_db),
        ):
            """
            Get a single record by ID.

            Args:
                item_id: The ID of the record to retrieve
                db: Database session (injected)

            Returns:
                The requested record

            Raises:
                HTTPException: 404 if record not found
            """
            item = db.query(model).filter(model.id == item_id).first()

            if not item:
                raise HTTPException(
                    status_code=404,
                    detail=f"{model.__name__} with id {item_id} not found",
                )

            return item

    def _add_create_route(self, create_schema: type[BaseModel], response_schema: type[BaseModel], model: type[Any], get_db: Callable) -> None:
        """Add POST / route for creating a new record."""

        @self.router.post(
            "/",
            response_model=response_schema,
            status_code=201,
        )
        def create_item(
            item: create_schema,  # type: ignore[valid-type]
            db: Session = Depends(get_db),
        ):
            """
            Create a new record.

            Args:
                item: The data for creating the record (validated by Pydantic)
                db: Database session (injected)

            Returns:
                The newly created record

            Raises:
                HTTPException: 400 if validation fails or duplicate constraint violated
            """
            try:
                # Convert Pydantic model to dict
                item_data = item.model_dump()  # type: ignore[attr-defined]

                # Create SQLAlchemy model instance
                db_item = model(**item_data)

                # Add to database
                db.add(db_item)
                db.commit()
                db.refresh(db_item)

                return db_item

            except Exception as e:
                db.rollback()
                # Handle common database errors (e.g., unique constraint violations)
                error_msg = str(e)
                if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                    raise HTTPException(
                        status_code=400,
                        detail="Record with this data already exists",
                    ) from e
                # Re-raise other exceptions
                raise HTTPException(
                    status_code=400, detail=f"Failed to create record: {error_msg}"
                ) from e

    def _add_update_route(self, update_schema: type[BaseModel], response_schema: type[BaseModel], model: type[Any], get_db: Callable) -> None:
        """Add PUT /{id} route for updating an existing record."""

        @self.router.put(
            "/{item_id}",
            response_model=response_schema,
        )
        def update_item(
            item_id: int,
            item: update_schema,  # type: ignore[valid-type]
            db: Session = Depends(get_db),
        ):
            """
            Update an existing record.

            Args:
                item_id: The ID of the record to update
                item: The data for updating the record (validated by Pydantic)
                db: Database session (injected)

            Returns:
                The updated record

            Raises:
                HTTPException: 404 if record not found, 400 if validation fails
            """
            # First, check if the record exists
            db_item = db.query(model).filter(model.id == item_id).first()

            if not db_item:
                raise HTTPException(
                    status_code=404,
                    detail=f"{model.__name__} with id {item_id} not found",
                )

            try:
                # Convert Pydantic model to dict, excluding unset fields
                update_data = item.model_dump(exclude_unset=True)  # type: ignore[attr-defined]

                # Update only the provided fields
                for field, value in update_data.items():
                    setattr(db_item, field, value)

                db.commit()
                db.refresh(db_item)

                return db_item

            except Exception as e:
                db.rollback()
                # Handle common database errors
                error_msg = str(e)
                if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                    raise HTTPException(
                        status_code=400,
                        detail="Record with this data already exists",
                    ) from e
                # Re-raise other exceptions
                raise HTTPException(
                    status_code=400, detail=f"Failed to update record: {error_msg}"
                ) from e

    def _add_delete_route(self, model: type[Any], get_db: Callable) -> None:
        """Add DELETE /{id} route for deleting a record."""

        @self.router.delete(
            "/{item_id}",
            status_code=204,
        )
        def delete_item(
            item_id: int,
            db: Session = Depends(get_db),
        ):
            """
            Delete a record.

            Args:
                item_id: The ID of the record to delete
                db: Database session (injected)

            Returns:
                None (204 No Content)

            Raises:
                HTTPException: 404 if record not found
            """
            # First, check if the record exists
            db_item = db.query(model).filter(model.id == item_id).first()

            if not db_item:
                raise HTTPException(
                    status_code=404,
                    detail=f"{model.__name__} with id {item_id} not found",
                )

            try:
                db.delete(db_item)
                db.commit()
                # Return None for 204 No Content
                return None

            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to delete record: {str(e)}"
                ) from e

    def _add_documentation_route(self) -> None:
        """Add GET /documentation route for API documentation."""

        @self.router.get(
            "/documentation",
            response_class=JSONResponse,
            tags=["Documentation"],
            summary=f"Get {self.model.__name__} API Documentation",
        )
        def get_documentation():
            """
            Get comprehensive documentation for this resource's API endpoints.

            Returns information about:
            - Available endpoints
            - Request/response schemas
            - Database model structure
            - Query parameters
            """
            # Get model columns information
            mapper = inspect(self.model)
            columns_info = {}

            for column in mapper.columns:
                columns_info[column.name] = {
                    "type": str(column.type),
                    "nullable": column.nullable,
                    "primary_key": column.primary_key,
                    "unique": column.unique if hasattr(column, 'unique') else False,
                    "indexed": column.index if hasattr(column, 'index') else False,
                }

            # Get schema information
            create_fields = {}
            response_fields = {}

            if hasattr(self.create_schema, 'model_fields'):
                for field_name, field_info in self.create_schema.model_fields.items():
                    create_fields[field_name] = {
                        "type": str(field_info.annotation),
                        "required": field_info.is_required(),
                        "description": field_info.description or "",
                    }

            if hasattr(self.response_schema, 'model_fields'):
                for field_name, field_info in self.response_schema.model_fields.items():
                    response_fields[field_name] = {
                        "type": str(field_info.annotation),
                        "description": field_info.description or "",
                    }

            return {
                "resource": self.model.__name__,
                "table_name": self.model.__tablename__,
                "endpoints": {
                    "list": {
                        "method": "GET",
                        "path": "/",
                        "description": "List all records with pagination",
                        "query_parameters": {
                            "skip": {
                                "type": "integer",
                                "default": 0,
                                "description": "Number of records to skip"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 100,
                                "min": 1,
                                "max": 1000,
                                "description": "Maximum number of records to return"
                            }
                        },
                        "response": f"List[{self.response_schema.__name__}]"
                    },
                    # Placeholder for future endpoints
                    "get": {
                        "method": "GET",
                        "path": "/{id}",
                        "description": "Get a single record by ID",
                        "path_parameters": {
                            "id": {
                                "type": "integer",
                                "description": "ID of the record to retrieve"
                            }
                        },
                        "response": self.response_schema.__name__
                    },
                    "create": {
                        "method": "POST",
                        "path": "/",
                        "description": "Create a new record",
                        "request_body": self.create_schema.__name__,
                        "response": self.response_schema.__name__,
                        "status_code": 201
                    },
                    "update": {
                        "method": "PUT",
                        "path": "/{id}",
                        "description": "Update an existing record (partial updates supported)",
                        "path_parameters": {
                            "id": {
                                "type": "integer",
                                "description": "ID of the record to update"
                            }
                        },
                        "request_body": self.update_schema.__name__,
                        "response": self.response_schema.__name__
                    },
                    "delete": {
                        "method": "DELETE",
                        "path": "/{id}",
                        "description": "Delete a record",
                        "path_parameters": {
                            "id": {
                                "type": "integer",
                                "description": "ID of the record to delete"
                            }
                        },
                        "status_code": 204,
                        "response": "No content"
                    }
                },
                "schemas": {
                    "create": {
                        "name": self.create_schema.__name__,
                        "fields": create_fields
                    },
                    "update": {
                        "name": self.update_schema.__name__,
                        "description": "Same as create schema. All fields are optional for partial updates."
                    },
                    "response": {
                        "name": self.response_schema.__name__,
                        "fields": response_fields
                    }
                },
                "database_model": {
                    "columns": columns_info
                }
            }
