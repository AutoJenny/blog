"""
Knowledge Base Operations Manual
Provides indexed, navigable view of system documentation
"""

from flask import Blueprint, render_template, request, jsonify
import os
import logging

bp = Blueprint('knowledge_base', __name__, url_prefix='/kb')
logger = logging.getLogger(__name__)

# Knowledge Base structure - defines the navigation hierarchy
KB_STRUCTURE = {
    'getting_started': {
        'title': 'Getting Started',
        'icon': '🏠',
        'pages': {
            'overview': {
                'title': 'System Overview',
                'template': 'knowledge_base/getting_started/overview.html'
            },
            'navigation': {
                'title': 'Quick Navigation Guide',
                'template': 'knowledge_base/getting_started/navigation.html'
            },
            'status': {
                'title': 'Development Status Dashboard',
                'template': 'knowledge_base/getting_started/status.html'
            },
            'common_tasks': {
                'title': 'Common Tasks',
                'template': 'knowledge_base/getting_started/common_tasks.html'
            }
        }
    },
    'content_types': {
        'title': 'Content Types',
        'icon': '📝',
        'pages': {
            'overview': {
                'title': 'Post Types Overview',
                'template': 'knowledge_base/content_types/overview.html'
            },
            'weekly_words_phrases': {
                'title': 'Weekly Words & Phrases',
                'template': 'knowledge_base/content_types/weekly_words_phrases.html',
                'subpages': {
                    'words': {
                        'title': 'Weekly Words',
                        'template': 'knowledge_base/content_types/weekly_words.html'
                    },
                    'phrases': {
                        'title': 'Weekly Phrases',
                        'template': 'knowledge_base/content_types/weekly_phrases.html'
                    },
                    'insults': {
                        'title': 'Weekly Insults',
                        'template': 'knowledge_base/content_types/weekly_insults.html'
                    }
                }
            },
            'weekly_blog_entries': {
                'title': 'Weekly Blog Entries',
                'template': 'knowledge_base/content_types/weekly_blog_entries.html',
                'status': 'planned'
            },
            'themed': {
                'title': 'Themed Posts',
                'template': 'knowledge_base/content_types/themed.html',
                'status': 'planned'
            },
            'recipe': {
                'title': 'Recipe Posts',
                'template': 'knowledge_base/content_types/recipe.html',
                'status': 'planned'
            },
            'profile': {
                'title': 'Profile Posts',
                'template': 'knowledge_base/content_types/profile.html',
                'status': 'planned'
            },
            'generated': {
                'title': 'Generated Posts',
                'template': 'knowledge_base/content_types/generated.html',
                'status': 'in_progress'
            }
        }
    },
    'channels': {
        'title': 'Output Channels',
        'icon': '📤',
        'pages': {
            'overview': {
                'title': 'Channels Overview',
                'template': 'knowledge_base/channels/overview.html'
            },
            'facebook': {
                'title': 'Facebook',
                'template': 'knowledge_base/channels/facebook.html'
            },
            'blog': {
                'title': 'Blog',
                'template': 'knowledge_base/channels/blog.html',
                'status': 'in_progress'
            },
            'instagram': {
                'title': 'Instagram',
                'template': 'knowledge_base/channels/instagram.html',
                'status': 'planned'
            },
            'twitter': {
                'title': 'Twitter',
                'template': 'knowledge_base/channels/twitter.html',
                'status': 'planned'
            },
            'newsletter': {
                'title': 'Newsletter',
                'template': 'knowledge_base/channels/newsletter.html',
                'status': 'in_progress'
            }
        }
    },
    'interfaces': {
        'title': 'Management Interfaces',
        'icon': '🎯',
        'pages': {
            'overview': {
                'title': 'Interfaces Overview',
                'template': 'knowledge_base/interfaces/overview.html'
            },
            'planning': {
                'title': 'Planning Interface',
                'template': 'knowledge_base/interfaces/planning.html'
            },
            'authoring': {
                'title': 'Authoring Interface',
                'template': 'knowledge_base/interfaces/authoring.html'
            },
            'imaging': {
                'title': 'Imaging Interface',
                'template': 'knowledge_base/interfaces/imaging.html'
            },
            'header': {
                'title': 'Header Interface',
                'template': 'knowledge_base/interfaces/header.html'
            },
            'publication_dashboard': {
                'title': 'Publication Dashboard',
                'template': 'knowledge_base/interfaces/publication_dashboard.html'
            },
            'monitoring': {
                'title': 'Monitoring System',
                'template': 'knowledge_base/interfaces/monitoring.html'
            },
            'launchpad': {
                'title': 'Launchpad',
                'template': 'knowledge_base/interfaces/launchpad.html'
            }
        }
    },
    'workflows': {
        'title': 'Workflows & Automation',
        'icon': '⚙️',
        'pages': {
            'overview': {
                'title': 'Workflow Overview',
                'template': 'knowledge_base/workflows/overview.html'
            },
            'stages': {
                'title': 'Stage System',
                'template': 'knowledge_base/workflows/stages.html'
            },
            'weekly_automation': {
                'title': 'Weekly Content Automation',
                'template': 'knowledge_base/workflows/weekly_automation.html'
            },
            'product_automation': {
                'title': 'Product Post Automation',
                'template': 'knowledge_base/workflows/product_automation.html'
            },
            'posting_queue': {
                'title': 'Posting Queue System',
                'template': 'knowledge_base/workflows/posting_queue.html'
            }
        }
    },
    'backend': {
        'title': 'Backend Systems',
        'icon': '🔧',
        'pages': {
            'overview': {
                'title': 'Backend Overview',
                'template': 'knowledge_base/backend/overview.html'
            },
            'database': {
                'title': 'Database Architecture',
                'template': 'knowledge_base/backend/database.html'
            },
            'apis': {
                'title': 'API Endpoints',
                'template': 'knowledge_base/backend/apis.html'
            },
            'services': {
                'title': 'Services & Utilities',
                'template': 'knowledge_base/backend/services.html'
            }
        }
    },
    'technical': {
        'title': 'Technical Reference',
        'icon': '📖',
        'pages': {
            'overview': {
                'title': 'Technical Overview',
                'template': 'knowledge_base/technical/overview.html'
            },
            'file_structure': {
                'title': 'File Structure',
                'template': 'knowledge_base/technical/file_structure.html'
            },
            'blueprints': {
                'title': 'Blueprint Organization',
                'template': 'knowledge_base/technical/blueprints.html'
            }
        }
    }
}


def get_status_badge(status):
    """Return status badge HTML"""
    badges = {
        'complete': '<span class="status-badge status-complete">✅ Complete</span>',
        'in_progress': '<span class="status-badge status-in-progress">🟡 In Progress</span>',
        'planned': '<span class="status-badge status-planned">🔴 Planned</span>',
        'deprecated': '<span class="status-badge status-deprecated">⚠️ Deprecated</span>'
    }
    return badges.get(status, '')


# Make function available to templates
@bp.app_template_filter('status_badge')
def status_badge_filter(status):
    """Template filter for status badges"""
    return get_status_badge(status)


@bp.context_processor
def inject_status_badge():
    """Make get_status_badge available to all templates"""
    return dict(get_status_badge=get_status_badge)


@bp.route('/')
def index():
    """Knowledge Base home page"""
    return render_template('knowledge_base/index.html', structure=KB_STRUCTURE, section=None, page=None, page_data=None)


@bp.route('/<section>/<page>')
def page(section, page):
    """Render a KB page"""
    if section not in KB_STRUCTURE:
        return render_template('knowledge_base/404.html'), 404
    
    section_data = KB_STRUCTURE[section]
    if page not in section_data['pages']:
        return render_template('knowledge_base/404.html'), 404
    
    page_data = section_data['pages'][page]
    template = page_data.get('template')
    
    if not template:
        return render_template('knowledge_base/404.html'), 404
    
    # Check if template exists
    template_path = os.path.join('templates', template)
    if not os.path.exists(template_path):
        logger.warning(f"KB template not found: {template_path}")
        return render_template('knowledge_base/coming_soon.html', 
                             section=section, page=page, 
                             page_data=page_data, structure=KB_STRUCTURE), 200
    
    return render_template(template, 
                         section=section, 
                         page=page,
                         page_data=page_data,
                         structure=KB_STRUCTURE,
                         get_status_badge=get_status_badge)


@bp.route('/api/structure')
def api_structure():
    """API endpoint to get KB structure (for search, etc.)"""
    return jsonify({
        'success': True,
        'structure': KB_STRUCTURE
    })


@bp.route('/search')
def search():
    """Full-text search across KB pages"""
    query = request.args.get('q', '').strip()
    if not query:
        return render_template('knowledge_base/search.html', 
                             query='', results=[], structure=KB_STRUCTURE,
                             section=None, page=None, page_data=None)
    
    # TODO: Implement full-text search
    # For now, return search page
    results = []
    return render_template('knowledge_base/search.html',
                         query=query,
                         results=results,
                         structure=KB_STRUCTURE,
                         section=None, page=None, page_data=None)
