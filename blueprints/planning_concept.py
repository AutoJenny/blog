"""
Planning Concept Module

Contains concept development route functions extracted from planning.py
"""

from flask import render_template
import logging

logger = logging.getLogger(__name__)

def planning_concept_brainstorm(post_id):
    """Brainstorm page"""
    return render_template('planning/concept/brainstorm.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_concept_section_structure(post_id):
    """Section structure page"""
    return render_template('planning/concept/section_structure.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_concept_topic_allocation(post_id):
    """Topic allocation page"""
    return render_template('planning/concept/topic_allocation.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_concept_titling(post_id):
    """Titling page"""
    return render_template('planning/concept/titling.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_concept_outline(post_id):
    """Outline page"""
    return render_template('planning/concept/outline.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_research_sources(post_id):
    """Research sources page"""
    return render_template('planning/research/sources.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_research_visuals(post_id):
    """Research visuals page"""
    return render_template('planning/research/visuals.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_research_prompts(post_id):
    """Research prompts page"""
    return render_template('planning/research/prompts.html', 
                          post_id=post_id, blueprint_name='planning')

def planning_research_verification(post_id):
    """Research verification page"""
    return render_template('planning/research/verification.html', 
                          post_id=post_id, blueprint_name='planning')