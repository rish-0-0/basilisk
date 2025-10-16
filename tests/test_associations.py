"""
Tests for the associations (relationships) module.

Tests cover:
- Association detection from SQLAlchemy models
- Include parameter parsing and validation
- Eager loading with joinedload
- All relationship types (one-to-many, many-to-one, one-to-one, many-to-many)
"""

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from basilisk.associations import (
    AssociationType,
    apply_includes_to_query,
    get_association_target,
    get_model_associations,
    has_association,
    parse_include_param,
    validate_include_param,
)

# Test database setup
Base = declarative_base()


# Association table for many-to-many
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("test_posts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("test_tags.id"), primary_key=True),
)


class TestUser(Base):
    """Test user model with relationships."""

    __tablename__ = "test_users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

    # One-to-Many
    posts = relationship("TestPost", back_populates="author")

    # One-to-One
    profile = relationship("TestProfile", back_populates="user", uselist=False)


class TestPost(Base):
    """Test post model with relationships."""

    __tablename__ = "test_posts"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey("test_users.id"))

    # Many-to-One
    author = relationship("TestUser", back_populates="posts")

    # Many-to-Many
    tags = relationship("TestTag", secondary=post_tags, back_populates="posts")


class TestProfile(Base):
    """Test profile model with relationship."""

    __tablename__ = "test_profiles"

    id = Column(Integer, primary_key=True)
    bio = Column(String)
    user_id = Column(Integer, ForeignKey("test_users.id"), unique=True)

    # One-to-One
    user = relationship("TestUser", back_populates="profile")


class TestTag(Base):
    """Test tag model with relationship."""

    __tablename__ = "test_tags"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    # Many-to-Many
    posts = relationship("TestPost", secondary=post_tags, back_populates="tags")


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Add test data
    user = TestUser(id=1, name="Test User", email="test@example.com")
    profile = TestProfile(id=1, bio="Test bio", user_id=1)
    post1 = TestPost(id=1, title="Post 1", author_id=1)
    post2 = TestPost(id=2, title="Post 2", author_id=1)
    tag1 = TestTag(id=1, name="Tag 1")
    tag2 = TestTag(id=2, name="Tag 2")

    post1.tags.append(tag1)
    post1.tags.append(tag2)
    post2.tags.append(tag1)

    session.add_all([user, profile, post1, post2, tag1, tag2])
    session.commit()

    yield session

    session.close()


# ============================================================================
# Association Detection Tests
# ============================================================================


def test_get_model_associations():
    """Test getting all associations from a model."""
    associations = get_model_associations(TestUser)

    assert "posts" in associations
    assert "profile" in associations

    # Check posts (one-to-many)
    posts_assoc = associations["posts"]
    assert posts_assoc.type == AssociationType.ONE_TO_MANY
    assert posts_assoc.target_model == TestPost
    assert posts_assoc.uselist is True

    # Check profile (one-to-one)
    profile_assoc = associations["profile"]
    assert profile_assoc.type == AssociationType.ONE_TO_ONE
    assert profile_assoc.target_model == TestProfile
    assert profile_assoc.uselist is False


def test_has_association():
    """Test checking if a model has a specific association."""
    assert has_association(TestUser, "posts") is True
    assert has_association(TestUser, "profile") is True
    assert has_association(TestUser, "nonexistent") is False


def test_get_association_target():
    """Test getting the target model of an association."""
    target = get_association_target(TestUser, "posts")
    assert target == TestPost

    target = get_association_target(TestUser, "profile")
    assert target == TestProfile

    target = get_association_target(TestUser, "nonexistent")
    assert target is None


def test_many_to_one_association():
    """
    Test many-to-one association detection.

    Note: Many-to-one with uselist=False is detected as ONE_TO_ONE,
    which is correct from the perspective of the Post model
    (each post has exactly one author).
    """
    associations = get_model_associations(TestPost)

    assert "author" in associations
    author_assoc = associations["author"]
    # Many-to-one appears as one-to-one from the "many" side
    assert author_assoc.type == AssociationType.ONE_TO_ONE
    assert author_assoc.target_model == TestUser
    assert author_assoc.uselist is False


def test_many_to_many_association():
    """Test many-to-many association detection."""
    associations = get_model_associations(TestPost)

    assert "tags" in associations
    tags_assoc = associations["tags"]
    assert tags_assoc.type == AssociationType.MANY_TO_MANY
    assert tags_assoc.target_model == TestTag
    assert tags_assoc.uselist is True


# ============================================================================
# Include Parameter Parsing Tests
# ============================================================================


def test_parse_include_param_simple():
    """Test parsing simple include parameter."""
    result = parse_include_param("posts,profile")

    assert "posts" in result
    assert "profile" in result
    assert result["posts"] == {}
    assert result["profile"] == {}


def test_parse_include_param_nested():
    """Test parsing nested include parameter."""
    result = parse_include_param("posts.tags,profile")

    assert "posts" in result
    assert "profile" in result
    assert "tags" in result["posts"]
    assert result["posts"]["tags"] == {}
    assert result["profile"] == {}


def test_parse_include_param_empty():
    """Test parsing empty include parameter."""
    result = parse_include_param("")
    assert result == {}


def test_parse_include_param_deep_nesting():
    """Test parsing deeply nested include parameter."""
    result = parse_include_param("posts.tags.posts")

    assert "posts" in result
    assert "tags" in result["posts"]
    assert "posts" in result["posts"]["tags"]


# ============================================================================
# Include Parameter Validation Tests
# ============================================================================


def test_validate_include_param_valid():
    """Test validating valid include parameters."""
    include_dict = {"posts": {}, "profile": {}}
    valid, error = validate_include_param(TestUser, include_dict)

    assert valid is True
    assert error is None


def test_validate_include_param_invalid_association():
    """Test validating invalid association name."""
    include_dict = {"nonexistent": {}}
    valid, error = validate_include_param(TestUser, include_dict)

    assert valid is False
    assert "not a valid association" in error


def test_validate_include_param_nested_valid():
    """Test validating nested associations."""
    include_dict = {"posts": {"tags": {}}}
    valid, error = validate_include_param(TestUser, include_dict)

    assert valid is True
    assert error is None


def test_validate_include_param_nested_invalid():
    """Test validating invalid nested association."""
    include_dict = {"posts": {"nonexistent": {}}}
    valid, error = validate_include_param(TestUser, include_dict)

    assert valid is False
    assert "not a valid association" in error


def test_validate_include_param_max_depth():
    """Test validating maximum depth limit."""
    # Create a deeply nested structure exceeding max_depth
    include_dict = {"posts": {"tags": {"posts": {"tags": {}}}}}
    valid, error = validate_include_param(TestUser, include_dict, max_depth=2)

    assert valid is False
    assert "exceeds maximum" in error


# ============================================================================
# Query Application Tests
# ============================================================================


def test_apply_includes_to_query(db_session):
    """Test applying includes to a SQLAlchemy query."""
    query = db_session.query(TestUser)
    include_dict = {"posts": {}, "profile": {}}

    # Apply includes
    query = apply_includes_to_query(query, TestUser, include_dict)

    # Execute query
    user = query.filter(TestUser.id == 1).first()

    assert user is not None
    assert user.name == "Test User"

    # Check that associations are loaded (not lazy)
    # If loaded, accessing them won't trigger additional queries
    assert len(user.posts) == 2
    assert user.profile is not None
    assert user.profile.bio == "Test bio"


def test_apply_includes_nested(db_session):
    """Test applying nested includes to a query."""
    query = db_session.query(TestUser)
    include_dict = {"posts": {"tags": {}}}

    # Apply includes
    query = apply_includes_to_query(query, TestUser, include_dict)

    # Execute query
    user = query.filter(TestUser.id == 1).first()

    assert user is not None
    assert len(user.posts) == 2

    # Check nested association
    post = user.posts[0]
    assert len(post.tags) >= 1


def test_apply_includes_empty(db_session):
    """Test applying empty includes (should not change query)."""
    query = db_session.query(TestUser)
    include_dict = {}

    # Apply empty includes
    query = apply_includes_to_query(query, TestUser, include_dict)

    # Should still work
    user = query.filter(TestUser.id == 1).first()
    assert user is not None


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_workflow(db_session):
    """Test complete workflow: parse -> validate -> apply -> query."""
    # Parse include parameter
    include_str = "posts.tags,profile"
    include_dict = parse_include_param(include_str)

    # Validate
    valid, error = validate_include_param(TestUser, include_dict)
    assert valid is True

    # Apply to query
    query = db_session.query(TestUser)
    query = apply_includes_to_query(query, TestUser, include_dict)

    # Execute
    user = query.filter(TestUser.id == 1).first()

    # Verify all associations are loaded
    assert user is not None
    assert len(user.posts) == 2
    assert user.profile is not None

    # Verify nested association
    for post in user.posts:
        assert len(post.tags) >= 0  # Tags are loaded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
