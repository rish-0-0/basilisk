"""
MCP (Model Context Protocol) Router for AI Agent Integration.

This module provides specialized routes that expose API documentation and examples
in a format optimized for AI agents. When enabled, AI agents can read comprehensive
documentation to understand the API structure and usage patterns.

The MCP mode is completely opt-in and adds a dedicated set of routes under /.mcp/
that provide:
- Comprehensive API documentation
- Usage examples
- Schema information
- Query capabilities
- Best practices

Usage:
    from basilisk import CRUDRouter

    router = CRUDRouter(
        model=User,
        create_schema=UserCreate,
        response_schema=UserResponse,
        get_db=get_db,
        enable_mcp=True,  # Enable MCP mode
    )
"""

from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import inspect

try:
    from .associations import get_model_associations
    ASSOCIATIONS_AVAILABLE = True
except ImportError:
    ASSOCIATIONS_AVAILABLE = False
    get_model_associations = None  # type: ignore


class MCPRouter:
    """
    Generates MCP (Model Context Protocol) routes for AI agent integration.

    This router provides specialized endpoints that give AI agents comprehensive
    information about the API, including schemas, capabilities, examples, and
    best practices.

    All MCP routes are mounted under /.mcp/ prefix to avoid conflicts with
    regular API routes.

    Available MCP Endpoints:
    - GET /.mcp/overview - Complete API overview
    - GET /.mcp/schema - Detailed schema information
    - GET /.mcp/examples - Usage examples
    - GET /.mcp/capabilities - API capabilities and features
    - GET /.mcp/guide - Best practices guide for AI agents
    """

    def __init__(
        self,
        *,
        model: type[Any],
        create_schema: type[BaseModel],
        update_schema: type[BaseModel],
        response_schema: type[BaseModel],
        prefix: str = "",
        enable_associations: bool = False,
        enable_permissions: bool = False,
    ):
        """
        Initialize the MCP router.

        Args:
            model: SQLAlchemy model class
            create_schema: Pydantic schema for creating records
            update_schema: Pydantic schema for updating records
            response_schema: Pydantic schema for responses
            prefix: URL prefix for the parent router (e.g., "/users")
            enable_associations: Whether associations are enabled
            enable_permissions: Whether permissions/RBAC is enabled
        """
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.prefix = prefix
        self.enable_associations = enable_associations
        self.enable_permissions = enable_permissions

        # Create the MCP router
        self.router = APIRouter(prefix="/.mcp", tags=["MCP (AI Agent Context)"])

        # Add MCP routes
        self._add_overview_route()
        self._add_schema_route()
        self._add_examples_route()
        self._add_capabilities_route()
        self._add_guide_route()

    def _get_model_info(self) -> Dict[str, Any]:
        """Extract comprehensive model information."""
        mapper = inspect(self.model)

        columns_info = {}
        for column in mapper.columns:
            columns_info[column.name] = {
                "type": str(column.type),
                "python_type": str(column.type.python_type) if hasattr(column.type, 'python_type') else None,
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "unique": column.unique if hasattr(column, 'unique') else False,
                "indexed": column.index if hasattr(column, 'index') else False,
                "default": str(column.default) if column.default else None,
            }

        # Get associations if enabled
        associations_info = {}
        if self.enable_associations and ASSOCIATIONS_AVAILABLE:
            associations = get_model_associations(self.model)  # type: ignore
            for rel_name, assoc_info in associations.items():
                associations_info[rel_name] = {
                    "type": assoc_info.association_type.value,
                    "target_model": assoc_info.target_model.__name__,
                    "uselist": assoc_info.uselist,
                }

        return {
            "name": self.model.__name__,
            "table_name": self.model.__tablename__,
            "columns": columns_info,
            "associations": associations_info if associations_info else None,
        }

    def _get_schema_info(self, schema: type[BaseModel]) -> Dict[str, Any]:
        """Extract Pydantic schema information."""
        fields_info = {}

        if hasattr(schema, 'model_fields'):
            for field_name, field_info in schema.model_fields.items():
                fields_info[field_name] = {
                    "type": str(field_info.annotation),
                    "required": field_info.is_required(),
                    "description": field_info.description or "",
                    "default": str(field_info.default) if hasattr(field_info, 'default') else None,
                }

        return {
            "name": schema.__name__,
            "fields": fields_info,
            "doc": schema.__doc__ or "",
        }

    def _add_overview_route(self) -> None:
        """Add GET /.mcp/overview route."""

        @self.router.get(
            "/overview",
            response_class=JSONResponse,
            summary="MCP: Complete API Overview",
            description="Comprehensive overview of the API for AI agents",
        )
        def mcp_overview():
            """
            Get complete API overview optimized for AI agent understanding.

            This endpoint provides everything an AI agent needs to understand
            and interact with this API resource.
            """
            return {
                "resource": self.model.__name__,
                "description": f"CRUD API for {self.model.__name__} resource",
                "base_path": self.prefix,
                "model": self._get_model_info(),
                "schemas": {
                    "create": self._get_schema_info(self.create_schema),
                    "update": self._get_schema_info(self.update_schema),
                    "response": self._get_schema_info(self.response_schema),
                },
                "endpoints": {
                    "list": {
                        "method": "GET",
                        "path": f"{self.prefix}/",
                        "description": "List all records with pagination and filtering",
                        "supports": ["filtering", "ordering", "pagination", "field_selection", "aggregation"],
                    },
                    "get": {
                        "method": "GET",
                        "path": f"{self.prefix}/{{id}}",
                        "description": "Get a single record by ID",
                        "supports": ["associations"] if self.enable_associations else [],
                    },
                    "create": {
                        "method": "POST",
                        "path": f"{self.prefix}/",
                        "description": "Create a new record",
                        "requires_authentication": self.enable_permissions,
                    },
                    "update": {
                        "method": "PUT",
                        "path": f"{self.prefix}/{{id}}",
                        "description": "Update an existing record",
                        "supports": ["partial_updates"],
                        "requires_authentication": self.enable_permissions,
                    },
                    "delete": {
                        "method": "DELETE",
                        "path": f"{self.prefix}/{{id}}",
                        "description": "Delete a record",
                        "requires_authentication": self.enable_permissions,
                    },
                },
                "features": {
                    "associations": self.enable_associations,
                    "permissions": self.enable_permissions,
                    "advanced_querying": True,
                    "pagination": True,
                },
                "mcp_endpoints": {
                    "overview": f"{self.prefix}/.mcp/overview",
                    "schema": f"{self.prefix}/.mcp/schema",
                    "examples": f"{self.prefix}/.mcp/examples",
                    "capabilities": f"{self.prefix}/.mcp/capabilities",
                    "guide": f"{self.prefix}/.mcp/guide",
                },
            }

    def _add_schema_route(self) -> None:
        """Add GET /.mcp/schema route."""

        @self.router.get(
            "/schema",
            response_class=JSONResponse,
            summary="MCP: Detailed Schema Information",
            description="Complete schema details for AI agents",
        )
        def mcp_schema():
            """
            Get detailed schema information for all operations.

            Provides comprehensive schema details including field types,
            validation rules, relationships, and constraints.
            """
            return {
                "resource": self.model.__name__,
                "database_model": self._get_model_info(),
                "pydantic_schemas": {
                    "create": self._get_schema_info(self.create_schema),
                    "update": self._get_schema_info(self.update_schema),
                    "response": self._get_schema_info(self.response_schema),
                },
                "validation_notes": {
                    "create": "All required fields must be provided",
                    "update": "All fields are optional for partial updates",
                    "response": "Includes all model fields plus computed properties",
                },
            }

    def _add_examples_route(self) -> None:
        """Add GET /.mcp/examples route."""

        @self.router.get(
            "/examples",
            response_class=JSONResponse,
            summary="MCP: Usage Examples",
            description="Practical examples for AI agents",
        )
        def mcp_examples():
            """
            Get comprehensive usage examples.

            Provides real-world examples of how to use each endpoint,
            including query parameters, request bodies, and expected responses.
            """
            examples = {
                "resource": self.model.__name__,
                "base_url": f"http://api.example.com{self.prefix}",
                "examples": {
                    "list_all": {
                        "description": "List all records with default pagination",
                        "request": {
                            "method": "GET",
                            "url": f"{self.prefix}/",
                            "query_params": {},
                        },
                        "response": {
                            "status": 200,
                            "body": f"Array of {self.response_schema.__name__} objects",
                        },
                    },
                    "list_filtered": {
                        "description": "List records with filtering",
                        "request": {
                            "method": "GET",
                            "url": f"{self.prefix}/?status=active&category=electronics",
                            "query_params": {
                                "status": "active",
                                "category": "electronics",
                            },
                        },
                        "notes": "Multiple values per field supported: ?status=active,pending",
                    },
                    "list_with_ordering": {
                        "description": "List records with custom ordering",
                        "request": {
                            "method": "GET",
                            "url": f"{self.prefix}/?orderBy=name:asc,created_at:desc",
                            "query_params": {
                                "orderBy": "name:asc,created_at:desc",
                            },
                        },
                    },
                    "list_with_selection": {
                        "description": "Select specific fields only",
                        "request": {
                            "method": "GET",
                            "url": f"{self.prefix}/?select=id,name,email",
                            "query_params": {
                                "select": "id,name,email",
                            },
                        },
                        "notes": "Aliases supported: ?select=name;full_name,email;contact",
                    },
                    "list_with_aggregation": {
                        "description": "Aggregate data with grouping",
                        "request": {
                            "method": "GET",
                            "url": f"{self.prefix}/?select=category,count(id);total&groupBy=category",
                            "query_params": {
                                "select": "category,count(id);total",
                                "groupBy": "category",
                            },
                        },
                        "notes": "Supports: count, sum, avg, min, max",
                    },
                    "get_by_id": {
                        "description": "Get a single record by ID",
                        "request": {
                            "method": "GET",
                            "url": f"{self.prefix}/1",
                        },
                        "response": {
                            "status": 200,
                            "body": f"{self.response_schema.__name__} object",
                        },
                    },
                    "create": {
                        "description": "Create a new record",
                        "request": {
                            "method": "POST",
                            "url": f"{self.prefix}/",
                            "headers": {
                                "Content-Type": "application/json",
                            },
                            "body": f"{{...{self.create_schema.__name__} fields...}}",
                        },
                        "response": {
                            "status": 201,
                            "body": f"Created {self.response_schema.__name__} object",
                        },
                    },
                    "update": {
                        "description": "Update an existing record (partial updates supported)",
                        "request": {
                            "method": "PUT",
                            "url": f"{self.prefix}/1",
                            "headers": {
                                "Content-Type": "application/json",
                            },
                            "body": f"{{...{self.update_schema.__name__} fields (all optional)...}}",
                        },
                        "response": {
                            "status": 200,
                            "body": f"Updated {self.response_schema.__name__} object",
                        },
                    },
                    "delete": {
                        "description": "Delete a record",
                        "request": {
                            "method": "DELETE",
                            "url": f"{self.prefix}/1",
                        },
                        "response": {
                            "status": 204,
                            "body": "No content",
                        },
                    },
                },
            }

            # Add associations examples if enabled
            if self.enable_associations:
                examples["examples"]["list_with_associations"] = {
                    "description": "Include related data (eager loading)",
                    "request": {
                        "method": "GET",
                        "url": f"{self.prefix}/?include=posts,profile",
                        "query_params": {
                            "include": "posts,profile",
                        },
                    },
                    "notes": "Nested includes supported: ?include=posts.tags,profile",
                }
                examples["examples"]["get_with_associations"] = {
                    "description": "Get record with related data",
                    "request": {
                        "method": "GET",
                        "url": f"{self.prefix}/1?include=posts,profile",
                        "query_params": {
                            "include": "posts,profile",
                        },
                    },
                }

            return examples

    def _add_capabilities_route(self) -> None:
        """Add GET /.mcp/capabilities route."""

        @self.router.get(
            "/capabilities",
            response_class=JSONResponse,
            summary="MCP: API Capabilities",
            description="List of all supported features and capabilities",
        )
        def mcp_capabilities():
            """
            Get complete list of API capabilities.

            Describes what operations and features are available,
            helping AI agents understand what they can do with this API.
            """
            capabilities = {
                "resource": self.model.__name__,
                "operations": {
                    "create": {
                        "supported": True,
                        "description": "Create new records",
                        "requires_authentication": self.enable_permissions,
                    },
                    "read": {
                        "supported": True,
                        "description": "Read records (list and get by ID)",
                        "requires_authentication": False,
                    },
                    "update": {
                        "supported": True,
                        "description": "Update existing records",
                        "partial_updates": True,
                        "requires_authentication": self.enable_permissions,
                    },
                    "delete": {
                        "supported": True,
                        "description": "Delete records",
                        "requires_authentication": self.enable_permissions,
                    },
                },
                "querying": {
                    "filtering": {
                        "supported": True,
                        "description": "Filter records by field values",
                        "syntax": "?field=value or ?field=value1,value2",
                        "notes": "OR logic within field, AND logic across fields",
                    },
                    "ordering": {
                        "supported": True,
                        "description": "Sort results by one or more fields",
                        "syntax": "?orderBy=field1:asc,field2:desc",
                        "directions": ["asc", "desc"],
                    },
                    "pagination": {
                        "supported": True,
                        "description": "Paginate results",
                        "parameters": ["skip", "limit"],
                        "defaults": {"skip": 0, "limit": 100},
                        "max_limit": 1000,
                    },
                    "field_selection": {
                        "supported": True,
                        "description": "Select specific fields to return",
                        "syntax": "?select=field1,field2",
                        "aliases": "?select=field1;alias1,field2;alias2",
                    },
                    "aggregation": {
                        "supported": True,
                        "description": "Aggregate data with functions",
                        "functions": ["count", "sum", "avg", "min", "max"],
                        "syntax": "?select=count(id);total&groupBy=category",
                        "requires": "groupBy parameter",
                    },
                    "grouping": {
                        "supported": True,
                        "description": "Group results by one or more fields",
                        "syntax": "?groupBy=field1,field2",
                        "used_with": "aggregation functions",
                    },
                },
                "associations": {
                    "supported": self.enable_associations,
                    "description": "Include related data (eager loading)",
                    "syntax": "?include=relation1,relation2",
                    "nested": "?include=relation1.nested,relation2",
                    "max_depth": 3,
                } if self.enable_associations else None,
                "security": {
                    "sql_injection_protection": True,
                    "input_validation": True,
                    "parameterized_queries": True,
                    "column_name_validation": True,
                    "rbac": self.enable_permissions,
                },
            }

            return capabilities

    def _add_guide_route(self) -> None:
        """Add GET /.mcp/guide route."""

        @self.router.get(
            "/guide",
            response_class=JSONResponse,
            summary="MCP: AI Agent Guide",
            description="Best practices and guidelines for AI agents",
        )
        def mcp_guide():
            """
            Get best practices guide for AI agents.

            Provides guidelines, tips, and best practices for effectively
            using this API from an AI agent context.
            """
            guide = {
                "resource": self.model.__name__,
                "title": f"AI Agent Guide for {self.model.__name__} API",
                "sections": {
                    "getting_started": {
                        "title": "Getting Started",
                        "steps": [
                            f"1. Review the overview: GET {self.prefix}/.mcp/overview",
                            f"2. Understand the schema: GET {self.prefix}/.mcp/schema",
                            f"3. Check capabilities: GET {self.prefix}/.mcp/capabilities",
                            f"4. Review examples: GET {self.prefix}/.mcp/examples",
                            f"5. Start making requests to {self.prefix}/",
                        ],
                    },
                    "best_practices": {
                        "title": "Best Practices",
                        "tips": [
                            "Always validate input against the schema before making requests",
                            "Use pagination for large datasets (skip/limit parameters)",
                            "Use field selection (?select) to reduce response size",
                            "Apply filtering before pagination for better performance",
                            "Use appropriate HTTP status codes to handle errors",
                            "Check for 404 (Not Found) when accessing individual records",
                            "Handle 400 (Bad Request) for validation errors",
                            "For updates, use partial updates (only send changed fields)",
                        ],
                    },
                    "common_patterns": {
                        "title": "Common Usage Patterns",
                        "patterns": {
                            "search_and_filter": {
                                "description": "Search for specific records",
                                "example": f"GET {self.prefix}/?name=John&status=active",
                            },
                            "paginated_list": {
                                "description": "Get paginated results",
                                "example": f"GET {self.prefix}/?skip=0&limit=20",
                            },
                            "sorted_results": {
                                "description": "Get sorted results",
                                "example": f"GET {self.prefix}/?orderBy=created_at:desc",
                            },
                            "minimal_response": {
                                "description": "Get only needed fields",
                                "example": f"GET {self.prefix}/?select=id,name",
                            },
                            "statistics": {
                                "description": "Get aggregate statistics",
                                "example": f"GET {self.prefix}/?select=status,count(id);total&groupBy=status",
                            },
                        },
                    },
                    "error_handling": {
                        "title": "Error Handling",
                        "status_codes": {
                            "200": "Success (GET, PUT)",
                            "201": "Created (POST)",
                            "204": "No Content (DELETE)",
                            "400": "Bad Request (validation error)",
                            "401": "Unauthorized (authentication required)" if self.enable_permissions else None,
                            "403": "Forbidden (insufficient permissions)" if self.enable_permissions else None,
                            "404": "Not Found (record doesn't exist)",
                            "500": "Internal Server Error (unexpected error)",
                        },
                        "tips": [
                            "Always check status code before processing response",
                            "Read error messages for specific validation failures",
                            "For 404, verify the ID exists before retrying",
                            "For 400, check the error details for field-specific issues",
                        ],
                    },
                    "security": {
                        "title": "Security Considerations",
                        "notes": [
                            "All inputs are validated against Pydantic schemas",
                            "SQL injection protection is automatic",
                            "Column names are validated against the model",
                            "Parameterized queries are used throughout",
                        ] + ([
                            "Authentication is required for write operations",
                            "Permission checks are enforced",
                        ] if self.enable_permissions else []),
                    },
                    "advanced_features": {
                        "title": "Advanced Features",
                        "features": {
                            "complex_filtering": {
                                "description": "Combine multiple filters",
                                "example": f"GET {self.prefix}/?status=active,pending&priority=high",
                                "notes": "OR within field, AND across fields",
                            },
                            "field_aliases": {
                                "description": "Rename fields in response",
                                "example": f"GET {self.prefix}/?select=name;product_name,price;cost",
                            },
                            "multi_field_sorting": {
                                "description": "Sort by multiple criteria",
                                "example": f"GET {self.prefix}/?orderBy=priority:desc,created_at:asc",
                            },
                        } | ({
                            "associations": {
                                "description": "Include related data",
                                "example": f"GET {self.prefix}/?include=posts,profile",
                                "nested": f"GET {self.prefix}/?include=posts.tags",
                            },
                        } if self.enable_associations else {}),
                    },
                },
                "quick_reference": {
                    "base_path": self.prefix,
                    "operations": ["GET", "POST", "PUT", "DELETE"],
                    "pagination": "?skip=0&limit=100",
                    "filtering": "?field=value",
                    "ordering": "?orderBy=field:asc",
                    "selection": "?select=field1,field2",
                    "aggregation": "?select=count(id)&groupBy=field",
                } | ({"associations": "?include=relation1,relation2"} if self.enable_associations else {}),
            }

            return guide
