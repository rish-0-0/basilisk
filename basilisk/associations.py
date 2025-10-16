"""
Association (relationship) utilities for SQLAlchemy models.

This module is OPTIONAL and provides utilities to detect and work with
SQLAlchemy relationships (associations), supporting one-to-many, many-to-one,
one-to-one, and many-to-many relationships.

Usage is completely opt-in - the router will work fine without this module.
"""

from enum import Enum
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import RelationshipProperty


class AssociationType(Enum):
    """Types of SQLAlchemy associations/relationships."""

    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    ONE_TO_ONE = "one_to_one"
    MANY_TO_MANY = "many_to_many"


class AssociationInfo:
    """
    Information about a SQLAlchemy association/relationship.

    This class stores metadata about relationships between models.

    Attributes:
        name: Name of the relationship attribute
        type: Type of association (one-to-many, many-to-one, etc.)
        target_model: Target model class
        back_populates: Name of the back-populating relationship (if any)
        uselist: Whether the relationship returns a list
        secondary: Secondary table for many-to-many relationships (if any)
        foreign_keys: Foreign key columns

    Example:
        >>> info = AssociationInfo(
        ...     name="posts",
        ...     association_type=AssociationType.ONE_TO_MANY,
        ...     target_model=Post
        ... )
    """

    def __init__(
        self,
        name: str,
        association_type: AssociationType,
        target_model: type[Any],
        back_populates: str | None = None,
        uselist: bool = True,
        secondary: Any | None = None,
        foreign_keys: list[Any] | None = None,
    ):
        """Initialize association info."""
        self.name = name
        self.type = association_type
        self.target_model = target_model
        self.back_populates = back_populates
        self.uselist = uselist
        self.secondary = secondary
        self.foreign_keys = foreign_keys or []

    def __repr__(self) -> str:
        """String representation of association info."""
        return (
            f"AssociationInfo(name='{self.name}', type={self.type}, "
            f"target={self.target_model.__name__})"
        )


def get_model_associations(model: type[Any]) -> dict[str, AssociationInfo]:
    """
    Get all associations/relationships for a SQLAlchemy model.

    This function inspects a SQLAlchemy model and returns information about
    all defined relationships (associations).

    Args:
        model: SQLAlchemy model class

    Returns:
        Dictionary mapping association names to AssociationInfo objects

    Example:
        >>> associations = get_model_associations(User)
        >>> for name, info in associations.items():
        ...     print(f"{name}: {info.type}")
        posts: AssociationType.ONE_TO_MANY
        profile: AssociationType.ONE_TO_ONE
    """
    associations = {}
    mapper = inspect(model)

    for attr in mapper.attrs:
        if isinstance(attr, RelationshipProperty):
            assoc_info = _parse_association(attr)
            if assoc_info:
                associations[assoc_info.name] = assoc_info

    return associations


def _parse_association(rel_property: RelationshipProperty) -> AssociationInfo | None:
    """
    Parse a SQLAlchemy relationship property into AssociationInfo.

    Args:
        rel_property: SQLAlchemy RelationshipProperty object

    Returns:
        AssociationInfo object or None if parsing fails
    """
    try:
        name = rel_property.key
        target_model = rel_property.mapper.class_
        uselist = rel_property.uselist
        back_populates = rel_property.back_populates

        # Get secondary table (for many-to-many)
        secondary = rel_property.secondary if hasattr(rel_property, 'secondary') else None

        # Get foreign keys
        foreign_keys = list(rel_property.local_remote_pairs) if hasattr(rel_property, 'local_remote_pairs') else []

        # Determine association type
        association_type = _determine_association_type(
            rel_property, uselist, secondary
        )

        return AssociationInfo(
            name=name,
            association_type=association_type,
            target_model=target_model,
            back_populates=back_populates,
            uselist=uselist,
            secondary=secondary,
            foreign_keys=foreign_keys,
        )

    except Exception:
        # If we can't parse the association, return None
        return None


def _determine_association_type(
    rel_property: RelationshipProperty,
    uselist: bool,
    secondary: Any | None,
) -> AssociationType:
    """
    Determine the type of a SQLAlchemy association/relationship.

    Args:
        rel_property: SQLAlchemy RelationshipProperty object
        uselist: Whether the relationship returns a list
        secondary: Secondary table (for many-to-many)

    Returns:
        AssociationType enum value
    """
    # Many-to-many relationships have a secondary table
    if secondary is not None:
        return AssociationType.MANY_TO_MANY

    # One-to-one relationships have uselist=False
    if not uselist:
        return AssociationType.ONE_TO_ONE

    # Determine if it's one-to-many or many-to-one
    # One-to-many: Foreign key is on the related table
    # Many-to-one: Foreign key is on this table
    direction = rel_property.direction.name if hasattr(rel_property, 'direction') else None

    if direction == "ONETOMANY":
        return AssociationType.ONE_TO_MANY
    elif direction == "MANYTOONE":
        return AssociationType.MANY_TO_ONE
    else:
        # Default to one-to-many if uselist=True and we can't determine
        return AssociationType.ONE_TO_MANY


def has_association(model: type[Any], name: str) -> bool:
    """
    Check if a model has a specific association/relationship.

    Args:
        model: SQLAlchemy model class
        name: Name of the association to check

    Returns:
        True if association exists, False otherwise

    Example:
        >>> has_association(User, "posts")
        True
        >>> has_association(User, "nonexistent")
        False
    """
    associations = get_model_associations(model)
    return name in associations


def get_association_target(model: type[Any], name: str) -> type[Any] | None:
    """
    Get the target model of an association/relationship.

    Args:
        model: SQLAlchemy model class
        name: Name of the association

    Returns:
        Target model class or None if association doesn't exist

    Example:
        >>> target = get_association_target(User, "posts")
        >>> target.__name__
        'Post'
    """
    associations = get_model_associations(model)
    assoc_info = associations.get(name)
    return assoc_info.target_model if assoc_info else None


def parse_include_param(include_str: str) -> dict[str, Any]:
    """
    Parse an include parameter string into a nested dictionary structure.

    Supports nested includes like "posts.comments,profile".

    Args:
        include_str: Comma-separated list of associations to include
                    (e.g., "posts,profile" or "posts.comments,profile")

    Returns:
        Dictionary structure for SQLAlchemy joinedload

    Example:
        >>> parse_include_param("posts,profile")
        {'posts': {}, 'profile': {}}
        >>> parse_include_param("posts.comments,profile")
        {'posts': {'comments': {}}, 'profile': {}}
    """
    if not include_str:
        return {}

    result = {}

    # Split by comma to get individual include paths
    includes = [inc.strip() for inc in include_str.split(",")]

    for include_path in includes:
        # Split by dot to handle nested associations
        parts = include_path.split(".")

        # Build nested dictionary
        current = result
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]

    return result


def validate_include_param(
    model: type[Any],
    include_dict: dict[str, Any],
    max_depth: int = 3,
    current_depth: int = 0,
) -> tuple[bool, str | None]:
    """
    Validate that an include parameter only references valid associations.

    Prevents circular references and limits nesting depth for security.

    Args:
        model: SQLAlchemy model class
        include_dict: Parsed include dictionary from parse_include_param
        max_depth: Maximum nesting depth allowed (prevents infinite loops)
        current_depth: Current recursion depth (internal use)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> valid, error = validate_include_param(User, {"posts": {}, "profile": {}})
        >>> valid
        True
    """
    if current_depth > max_depth:
        return False, f"Include nesting depth exceeds maximum of {max_depth}"

    associations = get_model_associations(model)

    for assoc_name, nested_includes in include_dict.items():
        # Check if association exists on this model
        if assoc_name not in associations:
            return False, f"'{assoc_name}' is not a valid association on {model.__name__}"

        # If there are nested includes, validate them recursively
        if nested_includes:
            assoc_info = associations[assoc_name]
            target_model = assoc_info.target_model

            valid, error = validate_include_param(
                target_model, nested_includes, max_depth, current_depth + 1
            )

            if not valid:
                return False, error

    return True, None


def apply_includes_to_query(
    query: Any,
    model: type[Any],
    include_dict: dict[str, Any],
) -> Any:
    """
    Apply eager loading (joinedload) to a SQLAlchemy query based on include dict.

    This prevents N+1 query problems by loading relationships in a single query.

    Args:
        query: SQLAlchemy query object
        model: SQLAlchemy model class
        include_dict: Dictionary from parse_include_param

    Returns:
        Modified query with joinedload applied

    Example:
        >>> query = db.query(User)
        >>> include_dict = parse_include_param("posts,profile")
        >>> query = apply_includes_to_query(query, User, include_dict)
    """
    from sqlalchemy.orm import joinedload

    for assoc_name, nested_includes in include_dict.items():
        # Check if association exists
        if has_association(model, assoc_name):
            # Apply joinedload for this association
            load_option = joinedload(getattr(model, assoc_name))

            # Apply nested loads recursively
            if nested_includes:
                assoc_target = get_association_target(model, assoc_name)
                if assoc_target:
                    load_option = _apply_nested_loads(
                        load_option, assoc_target, nested_includes
                    )

            query = query.options(load_option)

    return query


def _apply_nested_loads(
    load_option: Any,
    model: type[Any],
    include_dict: dict[str, Any],
) -> Any:
    """
    Recursively apply nested joinedload options.

    Args:
        load_option: Current SQLAlchemy load option
        model: Current model class
        include_dict: Dictionary of nested includes

    Returns:
        Modified load option with nested loads applied
    """
    from sqlalchemy.orm import joinedload

    for assoc_name, nested_includes in include_dict.items():
        if has_association(model, assoc_name):
            # Chain the joinedload
            load_option = load_option.joinedload(getattr(model, assoc_name))

            # Continue nesting if needed
            if nested_includes:
                assoc_target = get_association_target(model, assoc_name)
                if assoc_target:
                    load_option = _apply_nested_loads(
                        load_option, assoc_target, nested_includes
                    )

    return load_option
