"""
Planning Blueprint - Simple Modular Version
Gradually migrating to modular structure
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from config.database import db_manager
import logging
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Create planning blueprint
bp = Blueprint('planning', __name__, url_prefix='/planning')

# Import the original functions for now
# We'll gradually move functions to modules
from blueprints.planning_original_backup import *

# For now, we'll use the original file but with a cleaner structure
# This is a stepping stone to full modularization

# Export the main blueprint
__all__ = ['bp']
