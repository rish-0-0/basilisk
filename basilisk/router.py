"""FastAPI router generator for CRUD operations."""

from typing import Type, Callable, List, Any, Dict
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from pydantic import BaseModel


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
        model: Type[Any],
        create_schema: Type[BaseModel],
        response_schema: Type[BaseModel],
        get_db: Callable,
        prefix: str = "",
        tags: List[str] | None = None,
    ):
        """Initialize the CRUD router."""
        self.model = model
        self.create_schema = create_schema
        self.response_schema = response_schema
        self.get_db = get_db

        # Create the FastAPI router
        self.router = APIRouter(prefix=prefix, tags=tags or [model.__name__])

        # Add routes
        self._add_list_route()
        self._add_documentation_route()

    def _add_list_route(self) -> None:
        """Add GET / route for listing records."""

        @self.router.get("/", response_model=List[self.response_schema])
        def list_items(
            skip: int = Query(0, ge=0, description="Number of records to skip"),
            limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
            db: Session = Depends(self.get_db),
        ):
            """List all records with pagination."""
            # Minimal implementation - just return empty list for now
            # This will be expanded with actual CRUD logic later
            items = db.query(self.model).offset(skip).limit(limit).all()
            return items

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
                        "status": "not_implemented",
                        "description": "Get a single record by ID"
                    },
                    "create": {
                        "method": "POST",
                        "path": "/",
                        "status": "not_implemented",
                        "description": "Create a new record"
                    },
                    "update": {
                        "method": "PUT",
                        "path": "/{id}",
                        "status": "not_implemented",
                        "description": "Update an existing record"
                    },
                    "delete": {
                        "method": "DELETE",
                        "path": "/{id}",
                        "status": "not_implemented",
                        "description": "Delete a record"
                    }
                },
                "schemas": {
                    "create": {
                        "name": self.create_schema.__name__,
                        "fields": create_fields
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
