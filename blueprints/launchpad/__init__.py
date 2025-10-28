# blueprints/launchpad/__init__.py
"""Modular launchpad blueprint structure."""

# Import from the old launchpad.py to maintain all existing functionality
from blueprints.launchpad_old import bp

# Note: This maintains backward compatibility while we extract modules
# Eventually we'll replace this import with modular sub-blueprint imports
