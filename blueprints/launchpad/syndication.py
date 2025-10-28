# blueprints/launchpad/syndication.py
"""Syndication-related routes and functionality."""

from flask import Blueprint, render_template, jsonify, request, redirect
import logging
from config.database import db_manager
import json
from datetime import datetime, date, time, timedelta
from blueprints.launchpad_utils import get_next_posting_slot

bp = Blueprint("syndication", __name__)
logger = logging.getLogger(__name__)

# TODO: Extract all syndication routes from launchpad_old.py