"""Tests for workflow navigation module."""

import pytest
from flask import url_for
from modules.nav.services import get_workflow_stages, get_workflow_context

def test_get_workflow_stages(app):
    """Test getting workflow stages."""
    with app.app_context():
        stages = get_workflow_stages()
        assert stages is not None
        assert isinstance(stages, list)
        assert len(stages) > 0
        assert all('id' in stage for stage in stages)
        assert all('name' in stage for stage in stages)
        assert all('description' in stage for stage in stages)
        assert all('stage_order' in stage for stage in stages)

def test_get_workflow_context(app):
    """Test getting workflow context."""
    with app.app_context():
        context = get_workflow_context()
        assert context is not None
        assert isinstance(context, dict)
        assert 'current_stage' in context
        assert 'current_substage' in context
        assert 'current_step' in context
        assert 'stages' in context
        assert 'substages' in context
        assert 'all_posts' in context
        assert 'post_id' in context

def test_nav_index(client):
    """Test navigation index view."""
    response = client.get(url_for('workflow_nav.nav_index', post_id=1))
    assert response.status_code == 200
    assert b'Planning' in response.data
    assert b'Writing' in response.data
    assert b'Publishing' in response.data

def test_stage_view(client):
    """Test stage view."""
    response = client.get(url_for('workflow_nav.stage', stage='planning', substage='idea', post_id=1))
    assert response.status_code == 200
    assert b'Planning' in response.data
    assert b'Idea' in response.data

def test_post_selection(client):
    """Test post selection."""
    response = client.get(url_for('workflow_nav.select_post', post_id=1))
    assert response.status_code == 200
    assert b'post-selector' in response.data

def test_workflow_context_processor(app):
    """Test workflow context processor."""
    with app.app_context():
        context = app.jinja_env.globals['workflow_context']()
        assert context is not None
        assert isinstance(context, dict)
        assert 'current_stage' in context
        assert 'current_substage' in context
        assert 'current_step' in context
        assert 'stages' in context
        assert 'substages' in context
        assert 'all_posts' in context
        assert 'post_id' in context

def test_nav_dev(client):
    """Test navigation development view."""
    response = client.get(url_for('workflow_nav.nav_dev'))
    assert response.status_code == 200
    assert b'Planning' in response.data
    assert b'Writing' in response.data
    assert b'Publishing' in response.data 