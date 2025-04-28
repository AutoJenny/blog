"""Test blog functionality."""

import pytest
from flask import url_for
from datetime import datetime, UTC
from app.models import (
    Post,
    Tag,
    Category,
    PostSection,
    PostDevelopment,
    WorkflowStage,
)


@pytest.fixture
def test_category():
    category = Category()
    category.name = "Test Category"
    category.slug = "test-category"
    category.description = "A test category"
    return category


@pytest.fixture
def test_tag():
    tag = Tag()
    tag.name = "Test Tag"
    tag.slug = "test-tag"
    tag.description = "Test tag"
    return tag


@pytest.mark.api
def test_blog_index(client):
    """Test blog index page."""
    response = client.get("/blog/")
    assert response.status_code == 200
    assert b"Posts" in response.data


@pytest.mark.api
def test_create_post(client):
    """Test post creation."""
    response = client.post("/blog/new", json={"basic_idea": "Test post creation"})
    assert response.status_code == 200
    data = response.get_json()
    assert "slug" in data

    # Verify post was created
    post = Post.query.filter_by(slug=data["slug"]).first()
    assert post is not None
    # Optionally, check workflow stage/sub-stage content here


@pytest.mark.api
def test_view_post(client):
    # Create post via API
    response = client.post("/blog/new", json={"basic_idea": "Test post for view"})
    assert response.status_code == 200
    data = response.get_json()
    slug = data["slug"]
    # Now view the post
    response = client.get(f"/blog/{slug}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["slug"] == slug


@pytest.mark.api
def test_update_post(client):
    # Create post via API
    response = client.post("/blog/new", json={"basic_idea": "Test post for update"})
    assert response.status_code == 200
    data = response.get_json()
    slug = data["slug"]
    # Update the post
    response = client.put(f"/blog/{slug}", json={"title": "Updated Title"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Updated Title"


@pytest.mark.api
def test_delete_post(client):
    # Create post via API
    response = client.post("/blog/new", json={"basic_idea": "Test post for delete"})
    assert response.status_code == 200
    data = response.get_json()
    slug = data["slug"]
    # Delete the post
    response = client.delete(f"/blog/{slug}")
    assert response.status_code == 200
    # Try to get the deleted post
    response = client.get(f"/blog/{slug}")
    assert response.status_code == 404


@pytest.mark.api
def test_workflow_transition(client):
    # Create post via API
    response = client.post(
        "/blog/new", json={"basic_idea": "Test post for workflow transition"}
    )
    assert response.status_code == 200
    data = response.get_json()
    slug = data["slug"]
    response = client.post(
        f"/api/v1/workflow/{slug}/transition",
        json={
            "target_stage": WorkflowStage.RESEARCH.value,
            "notes": "Testing transition",
        },
    )
    assert response.status_code == 200
    # Use new normalized workflow model for assertions
    # workflow_stages = PostWorkflowStage.query.filter_by(post_id=slug).all()
    # assert any(ws.stage_id for ws in workflow_stages)
