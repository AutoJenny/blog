import pytest
from flask import url_for
from unittest.mock import patch, MagicMock
from app.models import Post, PostSection, LLMInteraction
from datetime import datetime, UTC

@pytest.fixture
def mock_chain():
    with patch('app.llm.routes.create_idea_generation_chain') as mock:
        chain = MagicMock()
        chain.run.return_value = {
            'title': 'Test Title',
            'outline': ['Point 1', 'Point 2'],
            'keywords': ['test', 'blog']
        }
        mock.return_value = chain
        yield mock

@pytest.fixture
def test_post(db):
    post = Post(
        title='Test Post',
        content='Test content',
        created_at=datetime.now(UTC),
        author_id=1  # This will match our test user's ID
    )
    db.session.add(post)
    db.session.commit()
    return post

@pytest.fixture
def test_section(db, test_post):
    section = PostSection(
        post_id=test_post.id,
        title='Test Section',
        content='Initial content',
        position=1,
        content_type='text',
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    db.session.add(section)
    db.session.commit()
    return section

def test_generate_idea(client, mock_chain, auth):
    auth.login()
    response = client.post('/api/llm/generate-idea', json={
        'topic': 'Scottish Kilts',
        'style': 'informative',
        'audience': 'history enthusiasts'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'title' in data
    assert 'outline' in data
    assert 'keywords' in data
    
    # Verify interaction was recorded
    interaction = LLMInteraction.query.first()
    assert interaction is not None
    assert 'Scottish Kilts' in interaction.input_text

def test_expand_section(client, auth, test_section):
    auth.login()
    with patch('app.llm.routes.create_content_expansion_chain') as mock_chain:
        chain = MagicMock()
        chain.run.return_value = {
            'content': 'Expanded content',
            'keywords': ['expanded', 'test'],
            'social_media_snippets': {'twitter': 'Test tweet'}
        }
        mock_chain.return_value = chain
        
        response = client.post(f'/api/llm/expand-section/{test_section.id}', json={
            'tone': 'professional',
            'platforms': ['blog']
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['content'] == 'Expanded content'
        assert 'keywords' in data
        assert 'social_media_snippets' in data
        
        # Verify section was updated
        updated_section = PostSection.query.get(test_section.id)
        assert updated_section.content == 'Expanded content'

def test_optimize_seo(client, auth, test_post):
    auth.login()
    with patch('app.llm.routes.create_seo_optimization_chain') as mock_chain:
        chain = MagicMock()
        chain.run.return_value = {
            'title_suggestions': ['Better Title'],
            'meta_description': 'Optimized description',
            'keyword_suggestions': ['seo', 'optimization']
        }
        mock_chain.return_value = chain
        
        response = client.post(f'/api/llm/optimize-seo/{test_post.id}', json={
            'keywords': ['test', 'seo']
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'suggestions' in data
        assert 'title_suggestions' in data['suggestions']

def test_generate_social(client, auth, test_section):
    auth.login()
    with patch('app.llm.routes.generate_social_media_content') as mock_gen:
        mock_gen.return_value = {
            'twitter': 'Test tweet',
            'instagram': 'Test instagram post'
        }
        
        response = client.post(f'/api/llm/generate-social/{test_section.id}', json={
            'platforms': ['twitter', 'instagram']
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'twitter' in data
        assert 'instagram' in data
        
        # Verify snippets were saved
        updated_section = PostSection.query.get(test_section.id)
        assert 'twitter' in updated_section.social_media_snippets

def test_unauthorized_access(client):
    # Test all endpoints without login
    endpoints = [
        ('post', '/api/llm/generate-idea'),
        ('post', f'/api/llm/expand-section/1'),
        ('post', f'/api/llm/optimize-seo/1'),
        ('post', f'/api/llm/generate-social/1')
    ]
    
    for method, endpoint in endpoints:
        response = getattr(client, method)(endpoint, json={})
        assert response.status_code == 401  # Unauthorized 