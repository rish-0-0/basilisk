"""
GraphQL schema generation from Pydantic models and SQLAlchemy models.

This module provides utilities to automatically generate GraphQL schemas
from existing Pydantic models, making it easy to create GraphQL APIs
alongside REST APIs.
"""

from typing import get_args, get_origin

from pydantic import BaseModel


def python_type_to_graphql_type(python_type: type) -> str:
    """
    Convert Python type to GraphQL type string.

    Args:
        python_type: Python type annotation

    Returns:
        GraphQL type string (e.g., "String!", "Int", "[String]")
    """
    # Handle Optional types (Union with None)
    origin = get_origin(python_type)

    # Handle Union types (e.g., str | None, Union[str, None])
    if origin is type(str | None):  # UnionType
        args = get_args(python_type)
        # Filter out None type
        non_none_types = [arg for arg in args if arg is not type(None)]
        if len(non_none_types) == 1:
            return python_type_to_graphql_type(non_none_types[0])
        # Multiple non-None types - use String as fallback
        return "String"

    # Handle basic types
    type_mapping = {
        int: "Int",
        str: "String",
        float: "Float",
        bool: "Boolean",
    }

    # Get the actual type if it's a string representation
    if isinstance(python_type, str):
        if "int" in python_type.lower():
            return "Int"
        elif "str" in python_type.lower():
            return "String"
        elif "float" in python_type.lower():
            return "Float"
        elif "bool" in python_type.lower():
            return "Boolean"
        return "String"  # Default fallback

    return type_mapping.get(python_type, "String")


def generate_graphql_type_from_pydantic(
    model: type[BaseModel], type_name: str | None = None
) -> str:
    """
    Generate GraphQL type definition from Pydantic model.

    Args:
        model: Pydantic model class
        type_name: Optional custom type name (defaults to model.__name__)

    Returns:
        GraphQL type definition as string

    Example:
        >>> class UserCreate(BaseModel):
        ...     name: str
        ...     email: str
        ...     age: int | None = None
        >>>
        >>> schema = generate_graphql_type_from_pydantic(UserCreate)
        >>> print(schema)
        type UserCreate {
            name: String!
            email: String!
            age: Int
        }
    """
    type_name = type_name or model.__name__
    fields = []

    if hasattr(model, "model_fields"):
        for field_name, field_info in model.model_fields.items():
            graphql_type = python_type_to_graphql_type(field_info.annotation)

            # Add ! for required fields
            if field_info.is_required():
                graphql_type += "!"

            description = field_info.description
            if description:
                fields.append(f'    "{description}"')

            fields.append(f"    {field_name}: {graphql_type}")

    fields_str = "\n".join(fields)
    return f"type {type_name} {{\n{fields_str}\n}}"


def generate_graphql_input_from_pydantic(
    model: type[BaseModel], input_name: str | None = None
) -> str:
    """
    Generate GraphQL input type definition from Pydantic model.

    Input types are used for mutations (create, update operations).

    Args:
        model: Pydantic model class
        input_name: Optional custom input name (defaults to model.__name__ + "Input")

    Returns:
        GraphQL input type definition as string

    Example:
        >>> class UserCreate(BaseModel):
        ...     name: str
        ...     email: str
        >>>
        >>> schema = generate_graphql_input_from_pydantic(UserCreate)
        >>> print(schema)
        input UserCreateInput {
            name: String!
            email: String!
        }
    """
    input_name = input_name or f"{model.__name__}Input"
    fields = []

    if hasattr(model, "model_fields"):
        for field_name, field_info in model.model_fields.items():
            graphql_type = python_type_to_graphql_type(field_info.annotation)

            # Add ! for required fields
            if field_info.is_required():
                graphql_type += "!"

            fields.append(f"    {field_name}: {graphql_type}")

    fields_str = "\n".join(fields)
    return f"input {input_name} {{\n{fields_str}\n}}"


def generate_relay_types(resource_name: str) -> str:
    """
    Generate Relay-style connection and edge types.

    Args:
        resource_name: Name of the resource (e.g., "User")

    Returns:
        GraphQL type definitions for Relay pagination
    """
    return f"""type {resource_name}Edge {{
    node: {resource_name}!
    cursor: String!
}}

type PageInfo {{
    hasNextPage: Boolean!
    hasPreviousPage: Boolean!
    startCursor: String
    endCursor: String
}}

type {resource_name}Connection {{
    edges: [{resource_name}Edge!]!
    pageInfo: PageInfo!
    totalCount: Int!
}}"""


def generate_graphql_schema(
    response_model: type[BaseModel],
    create_model: type[BaseModel],
    update_model: type[BaseModel] | None = None,
    resource_name: str | None = None,
    enable_relay: bool = True,
) -> str:
    """
    Generate complete GraphQL schema with queries and mutations for a resource.

    Args:
        response_model: Pydantic model for responses
        create_model: Pydantic model for create operations
        update_model: Optional Pydantic model for update operations
        resource_name: Name of the resource (e.g., "User", "Post")

    Returns:
        Complete GraphQL schema definition

    Example:
        >>> schema = generate_graphql_schema(
        ...     response_model=UserResponse,
        ...     create_model=UserCreate,
        ...     update_model=UserUpdate,
        ...     resource_name="User"
        ... )
    """
    resource_name = resource_name or response_model.__name__.replace("Response", "")
    resource_lower = resource_name.lower()
    resource_plural = f"{resource_lower}s"

    # Generate types
    response_type = generate_graphql_type_from_pydantic(
        response_model, type_name=resource_name
    )
    create_input = generate_graphql_input_from_pydantic(
        create_model, input_name=f"{resource_name}CreateInput"
    )

    update_input = ""
    if update_model:
        update_input = generate_graphql_input_from_pydantic(
            update_model, input_name=f"{resource_name}UpdateInput"
        )

    # Generate WHERE input type for filtering
    where_input = f"""input {resource_name}WhereInput {{
    id: Int
    id_in: [Int]
    id_not: Int
    id_lt: Int
    id_lte: Int
    id_gt: Int
    id_gte: Int

    AND: [{resource_name}WhereInput]
    OR: [{resource_name}WhereInput]
    NOT: {resource_name}WhereInput
}}"""

    # Generate queries with optional Relay support
    relay_query = ""
    if enable_relay:
        relay_query = f"""
    {resource_plural}Connection(
        first: Int
        after: String
        last: Int
        before: String
        orderBy: [String]
        where: {resource_name}WhereInput
    ): {resource_name}Connection!"""

    queries = f"""type Query {{
    {resource_lower}(id: Int!): {resource_name}
    {resource_plural}(
        skip: Int = 0
        limit: Int = 100
        orderBy: [String]
        where: {resource_name}WhereInput
    ): [{resource_name}!]!{relay_query}
}}"""

    # Generate mutations
    mutations = f"""type Mutation {{
    create{resource_name}(input: {resource_name}CreateInput!): {resource_name}!"""

    if update_model:
        mutations += f"""
    update{resource_name}(id: Int!, input: {resource_name}UpdateInput!): {resource_name}!"""

    mutations += f"""
    delete{resource_name}(id: Int!): Boolean!
}}"""

    # Combine all parts
    schema_parts = [
        response_type,
        create_input,
    ]

    if update_input:
        schema_parts.append(update_input)

    schema_parts.append(where_input)

    # Add Relay types if enabled
    if enable_relay:
        schema_parts.append(generate_relay_types(resource_name))

    schema_parts.extend([queries, mutations])

    return "\n\n".join(schema_parts)
