from typing import Dict, List, TypedDict
from enum import Enum


class SubStageStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class SubStageDefinition(TypedDict):
    name: str
    description: str
    required: bool
    validation_rules: List[str]
    dependencies: List[str]


# Define workflow stages and their sub-stages
WORKFLOW_STAGES = {
    "idea": {
        "description": "Initial concept and basic idea formation",
        "sub_stages": {
            "basic_idea": {
                "name": "Basic Idea",
                "description": "Core concept of the post",
                "required": True,
                "validation_rules": ["basic_idea_not_empty"],
                "dependencies": [],
            },
            "audience_definition": {
                "name": "Audience Definition",
                "description": "Define target audience and their needs",
                "required": True,
                "validation_rules": ["audience_defined"],
                "dependencies": ["basic_idea"],
            },
            "value_proposition": {
                "name": "Value Proposition",
                "description": "Define what value this post provides",
                "required": True,
                "validation_rules": ["value_prop_defined"],
                "dependencies": ["audience_definition"],
            },
        },
    },
    "research": {
        "description": "Research and information gathering",
        "sub_stages": {
            "initial_research": {
                "name": "Initial Research",
                "description": "Basic topic research and fact-finding",
                "required": True,
                "validation_rules": ["research_notes_added"],
                "dependencies": [],
            },
            "expert_consultation": {
                "name": "Expert Consultation",
                "description": "Gathering expert opinions and insights",
                "required": False,
                "validation_rules": ["expert_notes_added"],
                "dependencies": ["initial_research"],
            },
            "fact_verification": {
                "name": "Fact Verification",
                "description": "Verify key facts and claims",
                "required": True,
                "validation_rules": ["facts_verified"],
                "dependencies": ["initial_research"],
            },
        },
    },
    "outlining": {
        "description": "Post structure and outline creation",
        "sub_stages": {
            "section_planning": {
                "name": "Section Planning",
                "description": "Define main sections and their goals",
                "required": True,
                "validation_rules": ["sections_defined"],
                "dependencies": [],
            },
            "flow_optimization": {
                "name": "Flow Optimization",
                "description": "Optimize content flow and structure",
                "required": True,
                "validation_rules": ["flow_reviewed"],
                "dependencies": ["section_planning"],
            },
            "resource_planning": {
                "name": "Resource Planning",
                "description": "Plan required images, media, and resources",
                "required": True,
                "validation_rules": ["resources_listed"],
                "dependencies": ["section_planning"],
            },
        },
    },
    "authoring": {
        "description": "Content writing and development",
        "sub_stages": {
            "first_draft": {
                "name": "First Draft",
                "description": "Initial content writing",
                "required": True,
                "validation_rules": ["content_not_empty"],
                "dependencies": [],
            },
            "technical_review": {
                "name": "Technical Review",
                "description": "Review technical accuracy",
                "required": True,
                "validation_rules": ["tech_reviewed"],
                "dependencies": ["first_draft"],
            },
            "readability_pass": {
                "name": "Readability Pass",
                "description": "Improve readability and flow",
                "required": True,
                "validation_rules": ["readability_checked"],
                "dependencies": ["first_draft"],
            },
        },
    },
    "images": {
        "description": "Image creation and optimization",
        "sub_stages": {
            "image_planning": {
                "name": "Image Planning",
                "description": "Plan required images and their purposes",
                "required": True,
                "validation_rules": ["image_plan_complete"],
                "dependencies": [],
            },
            "generation": {
                "name": "Image Generation",
                "description": "Create or source required images",
                "required": True,
                "validation_rules": ["images_generated"],
                "dependencies": ["image_planning"],
            },
            "optimization": {
                "name": "Image Optimization",
                "description": "Optimize images for web",
                "required": True,
                "validation_rules": ["images_optimized"],
                "dependencies": ["generation"],
            },
            "watermarking": {
                "name": "Watermarking",
                "description": "Add watermarks to images",
                "required": True,
                "validation_rules": ["images_watermarked"],
                "dependencies": ["optimization"],
            },
        },
    },
    "metadata": {
        "description": "SEO and metadata optimization",
        "sub_stages": {
            "basic_meta": {
                "name": "Basic Metadata",
                "description": "Add basic meta title and description",
                "required": True,
                "validation_rules": ["basic_meta_complete"],
                "dependencies": [],
            },
            "seo_optimization": {
                "name": "SEO Optimization",
                "description": "Optimize for search engines",
                "required": True,
                "validation_rules": ["seo_optimized"],
                "dependencies": ["basic_meta"],
            },
            "social_preview": {
                "name": "Social Preview",
                "description": "Optimize social media previews",
                "required": True,
                "validation_rules": ["social_preview_complete"],
                "dependencies": ["basic_meta"],
            },
        },
    },
    "review": {
        "description": "Content review and quality assurance",
        "sub_stages": {
            "self_review": {
                "name": "Self Review",
                "description": "Author's final review",
                "required": True,
                "validation_rules": ["self_reviewed"],
                "dependencies": [],
            },
            "peer_review": {
                "name": "Peer Review",
                "description": "Review by another team member",
                "required": False,
                "validation_rules": ["peer_reviewed"],
                "dependencies": ["self_review"],
            },
            "final_check": {
                "name": "Final Check",
                "description": "Final quality check",
                "required": True,
                "validation_rules": ["final_checked"],
                "dependencies": ["self_review"],
            },
        },
    },
    "publishing": {
        "description": "Content publishing and deployment",
        "sub_stages": {
            "scheduling": {
                "name": "Scheduling",
                "description": "Schedule publication date",
                "required": True,
                "validation_rules": ["schedule_set"],
                "dependencies": [],
            },
            "deployment": {
                "name": "Deployment",
                "description": "Deploy to production",
                "required": True,
                "validation_rules": ["deployed"],
                "dependencies": ["scheduling"],
            },
            "verification": {
                "name": "Verification",
                "description": "Verify published content",
                "required": True,
                "validation_rules": ["verified_live"],
                "dependencies": ["deployment"],
            },
        },
    },
    "updates": {
        "description": "Post-publication updates and maintenance",
        "sub_stages": {
            "feedback_collection": {
                "name": "Feedback Collection",
                "description": "Collect and analyze feedback",
                "required": True,
                "validation_rules": ["feedback_collected"],
                "dependencies": [],
            },
            "content_updates": {
                "name": "Content Updates",
                "description": "Make necessary updates",
                "required": False,
                "validation_rules": ["updates_applied"],
                "dependencies": ["feedback_collection"],
            },
            "version_control": {
                "name": "Version Control",
                "description": "Track content versions",
                "required": True,
                "validation_rules": ["version_tracked"],
                "dependencies": ["content_updates"],
            },
        },
    },
    "syndication": {
        "description": "Content syndication across platforms",
        "sub_stages": {
            "platform_selection": {
                "name": "Platform Selection",
                "description": "Select syndication platforms",
                "required": True,
                "validation_rules": ["platforms_selected"],
                "dependencies": [],
            },
            "content_adaptation": {
                "name": "Content Adaptation",
                "description": "Adapt content for platforms",
                "required": True,
                "validation_rules": ["content_adapted"],
                "dependencies": ["platform_selection"],
            },
            "distribution": {
                "name": "Distribution",
                "description": "Distribute across platforms",
                "required": True,
                "validation_rules": ["distributed"],
                "dependencies": ["content_adaptation"],
            },
            "engagement_tracking": {
                "name": "Engagement Tracking",
                "description": "Track engagement metrics",
                "required": True,
                "validation_rules": ["tracking_setup"],
                "dependencies": ["distribution"],
            },
        },
    },
}

# Define valid stage transitions
VALID_TRANSITIONS = {
    "idea": ["research"],
    "research": ["outlining", "idea"],
    "outlining": ["authoring", "research"],
    "authoring": ["images", "outlining"],
    "images": ["metadata", "authoring"],
    "metadata": ["review", "images"],
    "review": ["publishing", "metadata", "authoring"],
    "publishing": ["updates", "review"],
    "updates": ["syndication", "publishing"],
    "syndication": ["updates"],
}
