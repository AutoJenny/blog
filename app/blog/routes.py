from flask import render_template, jsonify, request, redirect, url_for, current_app
from app.blog import bp
from app.models import Post, WorkflowStatus, WorkflowStage
from app import db
from slugify import slugify
import logging
from datetime import datetime


@bp.route("/")
def index():
    posts = Post.query.filter_by(deleted=False).order_by(Post.created_at.desc()).all()
    return render_template("blog/index.html", posts=posts)


@bp.route("/new", methods=["POST"])
def new_post():
    try:
        data = request.get_json()
        if not data or "basic_idea" not in data:
            return jsonify({"error": "basic_idea is required"}), 400

        current_app.logger.debug(f"Creating new post with data: {data}")

        # Create a new post with a temporary title based on the basic idea
        temp_title = data["basic_idea"][:50] + "..."  # Use first 50 chars of basic idea
        base_slug = slugify(temp_title)

        # Ensure unique slug
        counter = 0
        slug = base_slug
        while Post.query.filter_by(slug=slug).first():
            counter += 1
            slug = f"{base_slug}-{counter}"

        try:
            # Create the post with all required fields
            post = Post()
            post.title = temp_title
            post.slug = slug
            post.basic_idea = data["basic_idea"]
            post.published = False
            post.deleted = False
            post.content = ""  # Initialize with empty content

            db.session.add(post)
            db.session.flush()  # This will assign an ID to the post

            # Create initial workflow status using the post ID
            workflow_status = WorkflowStatus()
            workflow_status.post_id = post.id
            workflow_status.current_stage = WorkflowStage.IDEA
            workflow_status.stage_data = {}

            db.session.add(workflow_status)
            db.session.commit()

            current_app.logger.debug("Successfully committed to database")
            return jsonify(
                {
                    "message": "Post created successfully",
                    "slug": post.slug,
                    "id": post.id,
                }
            )
        except Exception as e:
            current_app.logger.error(f"Database commit failed: {str(e)}")
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        current_app.logger.error(f"Error in new_post: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@bp.route("/develop/<slug>")
def develop(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()

    workflow_stages = {
        "idea": {
            "description": "Initial concept and planning phase",
            "sub_stages": {
                "concept": {
                    "name": "Core Concept",
                    "description": "Define the main idea and target audience",
                    "required": True,
                },
                "outline": {
                    "name": "Post Outline",
                    "description": "Create a basic structure and key points",
                    "required": True,
                },
                "research": {
                    "name": "Research Plan",
                    "description": "Identify key sources and research areas",
                    "required": False,
                },
            },
        },
        "research": {
            "description": "Gather and organize research materials",
            "sub_stages": {
                "sources": {
                    "name": "Source Collection",
                    "description": "Gather and validate primary sources",
                    "required": True,
                },
                "notes": {
                    "name": "Research Notes",
                    "description": "Compile and organize research findings",
                    "required": True,
                },
                "media": {
                    "name": "Media Collection",
                    "description": "Gather images, videos, and other media",
                    "required": False,
                },
            },
        },
        "draft": {
            "description": "Write and refine the post content",
            "sub_stages": {
                "first_draft": {
                    "name": "First Draft",
                    "description": "Write the initial complete draft",
                    "required": True,
                },
                "revision": {
                    "name": "Content Revision",
                    "description": "Review and revise for clarity and flow",
                    "required": True,
                },
                "media_integration": {
                    "name": "Media Integration",
                    "description": "Insert and caption media elements",
                    "required": True,
                },
            },
        },
        "review": {
            "description": "Quality assurance and improvements",
            "sub_stages": {
                "technical": {
                    "name": "Technical Review",
                    "description": "Check formatting, links, and technical accuracy",
                    "required": True,
                },
                "editorial": {
                    "name": "Editorial Review",
                    "description": "Review for style, tone, and grammar",
                    "required": True,
                },
                "fact_check": {
                    "name": "Fact Checking",
                    "description": "Verify claims and citations",
                    "required": True,
                },
            },
        },
        "publish": {
            "description": "Prepare and publish the post",
            "sub_stages": {
                "seo": {
                    "name": "SEO Optimization",
                    "description": "Optimize title, meta description, and keywords",
                    "required": True,
                },
                "preview": {
                    "name": "Final Preview",
                    "description": "Review the post in preview mode",
                    "required": True,
                },
                "schedule": {
                    "name": "Publication Schedule",
                    "description": "Set publication date and time",
                    "required": True,
                },
            },
        },
        "syndicate": {
            "description": "Share and promote the post",
            "sub_stages": {
                "social": {
                    "name": "Social Media",
                    "description": "Prepare and schedule social media posts",
                    "required": True,
                },
                "newsletter": {
                    "name": "Newsletter",
                    "description": "Create and schedule newsletter content",
                    "required": False,
                },
                "analytics": {
                    "name": "Analytics Setup",
                    "description": "Configure tracking and goals",
                    "required": True,
                },
            },
        },
    }

    return render_template(
        "blog/develop.html", post=post, workflow_stages=workflow_stages
    )


@bp.route("/test_insert", methods=["GET"])
def test_insert():
    try:
        # Try to create the simplest possible valid post
        post = Post()
        post.title = "Test Post"
        post.slug = "test-post"
        post.content = ""

        db.session.add(post)
        db.session.commit()

        return jsonify({"success": True, "message": "Test post created", "id": post.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
