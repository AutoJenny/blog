# blueprints/launchpad_syndication.py
from flask import Blueprint, render_template, jsonify, request, send_file, redirect, url_for
import logging
import json
import os
import requests
from datetime import datetime, date, time, timedelta
import pytz
from humanize import naturaltime
from config.database import db_manager
import psycopg

bp = Blueprint('launchpad_syndication', __name__)
logger = logging.getLogger(__name__)
