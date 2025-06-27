import pytest
from flask import Flask, render_template_string
from app import create_app
from bs4 import BeautifulSoup

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_workflow_base_template(client):
    """Test workflow base template."""
    response = client.get("/workflow/posts/1")
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check navigation structure
    nav = soup.find('nav', {'class': 'workflow-nav'})
    assert nav is not None
    
    # Check stage links
    stages = nav.find_all('a', {'class': 'workflow-stage'})
    assert len(stages) > 0
    
    # Check content area
    content = soup.find('div', {'class': 'workflow-content'})
    assert content is not None

def test_workflow_stage_template(client):
    """Test workflow stage template."""
    response = client.get("/workflow/posts/1/planning")
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check stage header
    header = soup.find('h1', {'class': 'stage-title'})
    assert header is not None
    assert 'planning' in header.text.lower()
    
    # Check substage navigation
    substages = soup.find_all('a', {'class': 'substage-link'})
    assert len(substages) > 0

def test_workflow_substage_template(client):
    """Test workflow substage template."""
    response = client.get("/workflow/posts/1/planning/idea")
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check substage content
    content = soup.find('div', {'class': 'substage-content'})
    assert content is not None
    
    # Check LLM panel
    llm_panel = soup.find('div', {'class': 'llm-panel'})
    assert llm_panel is not None

def test_url_generation(app):
    """Test URL generation in templates."""
    with app.test_request_context():
        # Test post URL
        template = "{{ url_for('workflow.post', post_id=1) }}"
        result = render_template_string(template)
        assert result == "/workflow/posts/1"
        
        # Test stage URL
        template = "{{ url_for('workflow.stage', post_id=1, stage='planning') }}"
        result = render_template_string(template)
        assert result == "/workflow/posts/1/planning"
        
        # Test substage URL
        template = "{{ url_for('workflow.substage', post_id=1, stage='planning', substage='idea') }}"
        result = render_template_string(template)
        assert result == "/workflow/posts/1/planning/idea"

def test_template_inheritance(client):
    """Test template inheritance chain."""
    response = client.get("/workflow/posts/1/planning/idea")
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check base template elements
    assert soup.find('nav', {'class': 'workflow-nav'}) is not None
    assert soup.find('div', {'class': 'workflow-content'}) is not None
    
    # Check stage template elements
    assert soup.find('div', {'class': 'stage-header'}) is not None
    assert soup.find('div', {'class': 'substage-nav'}) is not None
    
    # Check substage template elements
    assert soup.find('div', {'class': 'substage-content'}) is not None

def test_template_includes(client):
    """Test template includes."""
    response = client.get("/workflow/posts/1/planning/idea")
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check navigation include
    assert soup.find('nav', {'class': 'workflow-nav'}) is not None
    
    # Check LLM panel include
    assert soup.find('div', {'class': 'llm-panel'}) is not None 