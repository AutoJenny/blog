"""
Path Resolution Configuration
Handles dynamic path resolution for images and other assets across different environments
"""

import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PathResolver:
    """Resolves paths dynamically based on environment configuration"""
    
    def __init__(self):
        # Try environment variable first, then fall back to dynamic detection
        self.project_root = os.getenv('BLOG_PROJECT_ROOT') or self._find_project_root()
        self.images_base = os.path.join(self.project_root, 'blog-images')
        self.images_static = os.path.join(self.images_base, 'static')
        self.service_url = os.getenv('BLOG_IMAGES_SERVICE_URL', 'http://localhost:5005')
        
        # Log the resolved paths for debugging
        logger.info(f"PathResolver initialized:")
        logger.info(f"  Project root: {self.project_root}")
        logger.info(f"  Images base: {self.images_base}")
        logger.info(f"  Images static: {self.images_static}")
        logger.info(f"  Service URL: {self.service_url}")
        
        # Validate that the paths exist
        self._validate_paths()
    
    def _find_project_root(self):
        """Dynamically find project root by looking for blog-images directory"""
        current = Path(__file__).parent
        while current != current.parent:
            if (current / 'blog-images').exists():
                logger.info(f"Found project root at: {current}")
                return str(current)
            current = current.parent
        
        # Fallback to current working directory
        logger.warning("Could not find project root, using current working directory")
        return os.getcwd()
    
    def _validate_paths(self):
        """Validate that the resolved paths exist"""
        if not os.path.exists(self.project_root):
            logger.error(f"Project root does not exist: {self.project_root}")
            raise FileNotFoundError(f"Project root not found: {self.project_root}")
        
        if not os.path.exists(self.images_base):
            logger.error(f"Images base directory does not exist: {self.images_base}")
            raise FileNotFoundError(f"Images base directory not found: {self.images_base}")
        
        if not os.path.exists(self.images_static):
            logger.error(f"Images static directory does not exist: {self.images_static}")
            raise FileNotFoundError(f"Images static directory not found: {self.images_static}")
        
        logger.info("All paths validated successfully")
    
    def get_header_image_path(self, post_id, image_type='watermarked'):
        """Get the file system path for a header image"""
        return os.path.join(self.images_static, 'content', 'posts', str(post_id), 'header', image_type)
    
    def get_section_image_path(self, post_id, section_id, image_type='watermarked'):
        """Get the file system path for a section image"""
        return os.path.join(self.images_static, 'content', 'posts', str(post_id), 'sections', str(section_id), image_type)
    
    def get_header_image_url(self, post_id, image_type='watermarked'):
        """Get the web URL for a header image"""
        return f"{self.service_url}/static/content/posts/{post_id}/header/{image_type}"
    
    def get_section_image_url(self, post_id, section_id, image_type='watermarked'):
        """Get the web URL for a section image"""
        return f"{self.service_url}/static/content/posts/{post_id}/sections/{section_id}/{image_type}"
    
    def convert_web_path_to_filesystem(self, web_path):
        """Convert a web path to a file system path"""
        if web_path.startswith('/static/'):
            return os.path.join(self.images_static, web_path[8:])  # Remove '/static/' prefix
        elif web_path.startswith(self.service_url):
            # Convert service URL to file system path
            relative_path = web_path.replace(f"{self.service_url}/static/", "")
            return os.path.join(self.images_static, relative_path)
        else:
            # Assume it's already a file system path
            return web_path
    
    def convert_filesystem_path_to_web(self, fs_path):
        """Convert a file system path to a web URL"""
        if fs_path.startswith(self.images_static):
            relative_path = os.path.relpath(fs_path, self.images_static)
            return f"{self.service_url}/static/{relative_path}"
        else:
            return fs_path

# Global instance for easy import
path_resolver = PathResolver()
