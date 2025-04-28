import pytest
from flask import url_for
from unittest.mock import patch, MagicMock
from app.models import Post, PostSection, LLMInteraction
from datetime import datetime, UTC
from app import db


@pytest.fixture
def mock_chain():
    with patch("app.llm.routes.create_idea_generation_chain") as mock:
        chain = MagicMock()
        chain.run.return_value = {
            "title": "Test Title",
            "outline": ["Point 1", "Point 2"],
            "keywords": ["test", "blog"],
        }
        mock.return_value = chain
        yield mock


@pytest.fixture
def test_section(client):
    # Create a post via the API
    response = client.post(
        "/api/v1/posts",
        json={"title": "Test Post", "content": "Test content", "author_id": 1},
    )
    assert response.status_code == 201
    post_id = response.get_json()["id"]
    section = PostSection()
    section.post_id = post_id
    section.title = "Test Section"
    section.content = "Initial content"
    section.content_type = "text"
    section.position = 1
    db.session.add(section)
    db.session.commit()
    return section


def test_generate_idea(client, mock_chain):
    response = client.post(
        "/api/v1/llm/generate-idea",
        json={
            "topic": "Scottish Kilts",
            "style": "informative",
            "audience": "history enthusiasts",
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "title" in data
    assert "outline" in data
    assert "keywords" in data
    # Verify interaction was recorded
    interaction = LLMInteraction.query.first()
    assert interaction is not None
    assert "Scottish Kilts" in interaction.input_text


def test_expand_section(client, test_section):
    with patch("app.llm.routes.create_content_expansion_chain") as mock_chain:
        chain = MagicMock()
        chain.run.return_value = {
            "content": "Expanded content",
            "keywords": ["expanded", "test"],
            "social_media_snippets": {"twitter": "Test tweet"},
        }
        mock_chain.return_value = chain
        response = client.post(
            f"/api/v1/llm/expand-section/{test_section.id}",
            json={"tone": "professional", "platforms": ["blog"]},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["content"] == "Expanded content"
        assert "keywords" in data
        assert "social_media_snippets" in data
        # Verify section was updated
        updated_section = PostSection.query.get(test_section.id)
        assert updated_section is not None
        assert updated_section.content == "Expanded content"


def test_optimize_seo(client):
    # Create a post via the API
    response = client.post(
        "/api/v1/posts",
        json={"title": "Test Post", "content": "Test content", "author_id": 1},
    )
    assert response.status_code == 201
    post_id = response.get_json()["id"]
    with patch("app.llm.routes.create_seo_optimization_chain") as mock_chain:
        chain = MagicMock()
        chain.run.return_value = {
            "title_suggestions": ["Better Title"],
            "meta_description": "Optimized description",
            "keyword_suggestions": ["seo", "optimization"],
        }
        mock_chain.return_value = chain
        response = client.post(
            f"/api/v1/llm/optimize-seo/{post_id}", json={"keywords": ["test", "seo"]}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "suggestions" in data
        assert "title_suggestions" in data["suggestions"]


def test_generate_social(client, test_section):
    with patch("app.llm.routes.generate_social_media_content") as mock_gen:
        mock_gen.return_value = {
            "twitter": "Test tweet",
            "instagram": "Test instagram post",
        }
        response = client.post(
            f"/api/v1/llm/generate-social/{test_section.id}",
            json={"platforms": ["twitter", "instagram"]},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "twitter" in data
        assert "instagram" in data
        # Verify snippets were saved
        updated_section = PostSection.query.get(test_section.id)
        assert updated_section is not None
        assert updated_section.social_media_snippets is not None
        assert "twitter" in updated_section.social_media_snippets


def test_unauthorized_access(client):
    # Test all endpoints without login
    endpoints = [
        ("post", "/api/v1/llm/generate-idea"),
        ("post", f"/api/v1/llm/expand-section/1"),
        ("post", f"/api/v1/llm/optimize-seo/1"),
        ("post", f"/api/v1/llm/generate-social/1"),
    ]

    for method, endpoint in endpoints:
        response = getattr(client, method)(endpoint, json={})
        assert response.status_code == 200  # No authentication, should be 200
