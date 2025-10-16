"""Basilisk - Automatic CRUD route generation for FastAPI + SQLAlchemy."""

from .router import CRUDRouter
from .query_parser import QueryParser

# GraphQL support (optional - requires ariadne)
try:
    from .graphql_router import GraphQLCRUDRouter
    from .graphql_schema import (
        generate_graphql_input_from_pydantic,
        generate_graphql_schema,
        generate_graphql_type_from_pydantic,
    )

    __all__ = [
        "CRUDRouter",
        "QueryParser",
        "GraphQLCRUDRouter",
        "generate_graphql_schema",
        "generate_graphql_type_from_pydantic",
        "generate_graphql_input_from_pydantic",
    ]
except ImportError:
    # Ariadne not installed - GraphQL support not available
    __all__ = ["CRUDRouter", "QueryParser"]

__version__ = "0.1.0"
