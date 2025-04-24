"""Test blog functionality."""

import pytest
from flask import url_for
from datetime import datetime, UTC
from app.models import Post, Tag, Category, PostSection, WorkflowStatus, WorkflowStage


@pytest.fixture
def test_category(db):
    """Create a test category."""
    category = Category(
        name="Test Category", slug="test-category", description="A test category"
    )
    db.session.add(category)
    db.session.commit()
    return category


@pytest.fixture
def test_tag(db):
    """Create a test tag."""
    tag = Tag(name="Test Tag", slug="test-tag", description="A test tag")
    db.session.add(tag)
    db.session.commit()
    return tag


@pytest.fixture
def test_post(db, test_user, test_category, test_tag):
    """Create a test post with category and tag."""
    post = Post(
        title="Test Post",
        slug="test-post",
        content="Test content",
        summary="Test summary",
        concept="Test concept",
        basic_idea="Test idea",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    post.categories.append(test_category)
    post.tags.append(test_tag)

    # Add workflow status
    workflow = WorkflowStatus(
        current_stage=WorkflowStage.IDEA, stage_data={"notes": "Initial stage"}
    )
    post.workflow_status = workflow

    db.session.add(post)
    db.session.commit()
    return post


@pytest.mark.api
def test_blog_index(client):
    """Test blog index page."""
    response = client.get("/blog/")
    assert response.status_code == 200
    assert b"Posts" in response.data


@pytest.mark.api
def test_create_post(client, auth):
    """Test post creation."""
    auth.login()
    response = client.post("/blog/new", json={"basic_idea": "Test post creation"})
    assert response.status_code == 200
    data = response.get_json()
    assert "slug" in data

    # Verify post was created
    post = Post.query.filter_by(basic_idea="Test post creation").first()
    assert post is not None
    assert post.workflow_status.current_stage == WorkflowStage.IDEA


@pytest.mark.api
def test_view_post(client, test_post):
    """Test viewing a post."""
    response = client.get(f"/blog/develop/{test_post.slug}")
    assert response.status_code == 200
    assert test_post.title.encode() in response.data


@pytest.mark.api
def test_update_post(client, auth, test_post):
    """Test post update."""
    auth.login()
    new_title = "Updated Test Post"
    response = client.post(
        f"/blog/update/{test_post.id}",
        json={"title": new_title, "content": "Updated content"},
    )
    assert response.status_code == 200

    # Verify post was updated
    updated_post = Post.query.get(test_post.id)
    assert updated_post.title == new_title
    assert updated_post.content == "Updated content"


@pytest.mark.api
def test_delete_post(client, auth, test_post):
    """Test post deletion."""
    auth.login()
    response = client.post(f"/blog/delete/{test_post.id}")
    assert response.status_code == 200

    # Verify post was marked as deleted
    deleted_post = Post.query.get(test_post.id)
    assert deleted_post.deleted is True


@pytest.mark.api
def test_unauthorized_post_operations(client, test_post):
    """Test unauthorized post operations."""
    # Try operations without login
    endpoints = [
        ("post", "/blog/new"),
        ("post", f"/blog/update/{test_post.id}"),
        ("post", f"/blog/delete/{test_post.id}"),
    ]

    for method, endpoint in endpoints:
        response = getattr(client, method)(endpoint, json={})
        assert response.status_code == 401  # Unauthorized


@pytest.mark.api
def test_workflow_transition(client, auth, test_post):
    """Test workflow stage transition."""
    auth.login()
    response = client.post(
        f"/blog/workflow/{test_post.id}",
        json={"stage": WorkflowStage.RESEARCH.value, "notes": "Moving to research"},
    )
    assert response.status_code == 200

    # Verify workflow was updated
    post = Post.query.get(test_post.id)
    assert post.workflow_status.current_stage == WorkflowStage.RESEARCH
    assert len(post.workflow_status.history) == 1
