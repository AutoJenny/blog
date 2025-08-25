# DEPRECATED: This file is being replaced by direct SQL models and queries. All ORM code has been removed.
# Only enums, constants, and utility functions should remain here if needed.

from datetime import datetime
import enum
from jinja2 import Template
import subprocess
import os

# (Keep only enums/constants below if needed)

class WorkflowStage(str, enum.Enum):
    IDEA = "idea"
    RESEARCH = "research"
    OUTLINING = "outlining"
    AUTHORING = "authoring"
    IMAGES = "images"
    METADATA = "metadata"
    REVIEW = "review"
    PUBLISHING = "publishing"
    UPDATES = "updates"
    SYNDICATION = "syndication"

    def __str__(self):
        return self.value

# (Remove all ORM model classes and db usage)
