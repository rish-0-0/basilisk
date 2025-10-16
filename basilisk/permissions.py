"""
Role-Based Access Control (RBAC) system for Basilisk.

This module provides a flexible RBAC system for controlling access to CRUD operations.
It assumes that authentication is handled by the user's application and that user
context is available through FastAPI dependencies.

Example usage:
    # Define roles and permissions
    permissions = PermissionConfig(
        roles={
            "admin": ["create", "read", "update", "delete"],
            "editor": ["read", "update"],
            "viewer": ["read"]
        }
    )

    # Use with CRUDRouter
    router = CRUDRouter(
        model=User,
        create_schema=UserCreate,
        response_schema=UserResponse,
        get_db=get_db,
        permissions=permissions,
        get_current_user=get_current_user,  # Your auth dependency
    )
"""

from typing import Any, Callable, Dict, List, Optional, Set
from fastapi import HTTPException, Request
from pydantic import BaseModel


class UserContext(BaseModel):
    """
    Base user context model.

    Users should extend this or provide their own user model with at minimum:
    - id: User identifier
    - roles: List of role names

    Example:
        class MyUser(UserContext):
            id: int
            username: str
            roles: List[str]
            email: str
    """
    id: int | str
    roles: List[str] = []


class PermissionConfig:
    """
    Configuration for role-based permissions.

    Defines which roles can perform which operations (CRUD actions).

    Attributes:
        roles: Dictionary mapping role names to list of allowed operations
        custom_checks: Dictionary of custom permission check functions

    Example:
        config = PermissionConfig(
            roles={
                "admin": ["create", "read", "update", "delete"],
                "editor": ["read", "update"],
                "viewer": ["read"]
            },
            custom_checks={
                "update": lambda user, resource: user.id == resource.owner_id
            }
        )
    """

    def __init__(
        self,
        roles: Dict[str, List[str]] | None = None,
        custom_checks: Dict[str, Callable[[Any, Any], bool]] | None = None,
        allow_anonymous: Set[str] | None = None,
    ):
        """
        Initialize permission configuration.

        Args:
            roles: Dictionary mapping role names to allowed operations
            custom_checks: Dictionary of custom permission check functions
            allow_anonymous: Set of operations that don't require authentication
        """
        self.roles = roles or {}
        self.custom_checks = custom_checks or {}
        self.allow_anonymous = allow_anonymous or set()

    def is_allowed(
        self,
        operation: str,
        user: UserContext | None,
        resource: Any = None,
    ) -> bool:
        """
        Check if a user is allowed to perform an operation.

        Args:
            operation: Operation name (e.g., "create", "read", "update", "delete")
            user: User context (None for anonymous users)
            resource: Optional resource object for resource-level checks

        Returns:
            True if user is allowed, False otherwise
        """
        # Check if operation is allowed for anonymous users
        if operation in self.allow_anonymous:
            return True

        # If no user and operation not in allow_anonymous, deny
        if user is None:
            return False

        # Check role-based permissions
        for role in user.roles:
            if role in self.roles:
                if operation in self.roles[role]:
                    # Check custom permission function if exists
                    if operation in self.custom_checks:
                        return self.custom_checks[operation](user, resource)
                    return True

        return False


class PermissionChecker:
    """
    Dependency for checking permissions in FastAPI routes.

    Example:
        def get_current_user(request: Request) -> UserContext:
            # Your authentication logic here
            return UserContext(id=1, roles=["admin"])

        permission_checker = PermissionChecker(
            config=permission_config,
            get_current_user=get_current_user,
        )

        @router.get("/")
        async def list_items(
            user: UserContext = Depends(permission_checker.require("read"))
        ):
            # Route logic here
            pass
    """

    def __init__(
        self,
        config: PermissionConfig,
        get_current_user: Optional[Callable] = None,
    ):
        """
        Initialize permission checker.

        Args:
            config: Permission configuration
            get_current_user: Optional dependency for getting current user
        """
        self.config = config
        self.get_current_user = get_current_user

    def require(
        self,
        operation: str,
        error_message: str | None = None,
    ) -> Callable:
        """
        Create a FastAPI dependency that requires a specific permission.

        Args:
            operation: Operation name to check
            error_message: Optional custom error message

        Returns:
            FastAPI dependency function

        Example:
            @router.delete("/{id}")
            async def delete_item(
                id: int,
                user: UserContext = Depends(checker.require("delete"))
            ):
                pass
        """
        async def permission_dependency(request: Request) -> UserContext | None:
            # Get current user if dependency is provided
            user = None
            if self.get_current_user:
                try:
                    user = await self.get_current_user(request)
                except Exception:
                    # If get_current_user fails, treat as anonymous
                    pass

            # Check permission
            if not self.config.is_allowed(operation, user):
                raise HTTPException(
                    status_code=403,
                    detail=error_message or f"Permission denied: {operation} operation requires appropriate role",
                )

            return user

        return permission_dependency

    def check(
        self,
        operation: str,
        user: UserContext | None,
        resource: Any = None,
    ) -> None:
        """
        Check permission and raise HTTPException if denied.

        Args:
            operation: Operation name to check
            user: User context
            resource: Optional resource for resource-level checks

        Raises:
            HTTPException: If permission denied

        Example:
            checker.check("delete", current_user, item)
        """
        if not self.config.is_allowed(operation, user, resource):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: insufficient privileges for {operation}",
            )


def requires_role(*roles: str) -> Callable:
    """
    Decorator for requiring specific roles (simple version without PermissionConfig).

    This is a simpler alternative when you just want to check roles directly
    without setting up a full PermissionConfig.

    Args:
        *roles: Role names that are allowed

    Returns:
        Decorator function

    Example:
        @requires_role("admin", "editor")
        async def delete_item(
            id: int,
            user: UserContext = Depends(get_current_user)
        ):
            pass

    Note:
        This requires that the route has a parameter named 'user' with UserContext type.
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (assumes parameter named 'user')
            user = kwargs.get('user')

            if user is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required",
                )

            # Check if user has any of the required roles
            user_roles = set(user.roles if hasattr(user, 'roles') else [])
            required_roles = set(roles)

            if not user_roles.intersection(required_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: requires one of roles: {', '.join(roles)}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class ResourcePermissionChecker:
    """
    Permission checker for resource-level permissions (e.g., "user can only edit their own posts").

    Example:
        def can_edit_post(user: UserContext, post: Post) -> bool:
            return user.id == post.author_id or "admin" in user.roles

        checker = ResourcePermissionChecker(can_edit_post)

        # In your route:
        checker.check(current_user, post)
    """

    def __init__(self, permission_func: Callable[[UserContext, Any], bool]):
        """
        Initialize resource permission checker.

        Args:
            permission_func: Function that takes (user, resource) and returns bool
        """
        self.permission_func = permission_func

    def check(self, user: UserContext | None, resource: Any) -> None:
        """
        Check resource-level permission.

        Args:
            user: User context
            resource: Resource to check permission for

        Raises:
            HTTPException: If permission denied
        """
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
            )

        if not self.permission_func(user, resource):
            raise HTTPException(
                status_code=403,
                detail="Permission denied: insufficient privileges for this resource",
            )

    def require(self) -> Callable:
        """
        Create a dependency that checks resource permission.

        Returns:
            FastAPI dependency function
        """
        async def dependency(user: UserContext, resource: Any) -> None:
            self.check(user, resource)

        return dependency
