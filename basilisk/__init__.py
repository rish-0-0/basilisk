"""Basilisk - Automatic CRUD route generation for FastAPI + SQLAlchemy."""

from .router import CRUDRouter
from .query_parser import QueryParser

# Permissions support (RBAC) - optional
try:
    from .permissions import (
        PermissionChecker,
        PermissionConfig,
        ResourcePermissionChecker,
        UserContext,
        requires_role,
    )
    PERMISSIONS_AVAILABLE = True
except ImportError:
    PERMISSIONS_AVAILABLE = False

# GraphQL support - optional (requires ariadne)
try:
    from .graphql_router import GraphQLCRUDRouter
    from .graphql_schema import (
        generate_graphql_input_from_pydantic,
        generate_graphql_schema,
        generate_graphql_type_from_pydantic,
    )
    GRAPHQL_AVAILABLE = True
except ImportError:
    GRAPHQL_AVAILABLE = False

# Associations (relationships) support - optional
try:
    from .associations import (
        AssociationInfo,
        AssociationType,
        apply_includes_to_query,
        get_association_target,
        get_model_associations,
        has_association,
        parse_include_param,
        validate_include_param,
    )
    ASSOCIATIONS_AVAILABLE = True
except ImportError:
    ASSOCIATIONS_AVAILABLE = False

# Build __all__ dynamically based on available features
__all__ = ["CRUDRouter", "QueryParser"]

if PERMISSIONS_AVAILABLE:
    __all__.extend([
        "PermissionChecker",
        "PermissionConfig",
        "ResourcePermissionChecker",
        "UserContext",
        "requires_role",
    ])

if GRAPHQL_AVAILABLE:
    __all__.extend([
        "GraphQLCRUDRouter",
        "generate_graphql_schema",
        "generate_graphql_type_from_pydantic",
        "generate_graphql_input_from_pydantic",
    ])

if ASSOCIATIONS_AVAILABLE:
    __all__.extend([
        "AssociationInfo",
        "AssociationType",
        "apply_includes_to_query",
        "get_association_target",
        "get_model_associations",
        "has_association",
        "parse_include_param",
        "validate_include_param",
    ])

__version__ = "0.3.0"
