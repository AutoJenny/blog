from flask import render_template, jsonify, request, redirect, url_for, abort
from app.blog import bp
from app.models import Post, PostDevelopment, PostSection
from app import db
from slugify import slugify
import logging
from datetime import datetime
from app.blog.fields import WORKFLOW_FIELDS


@bp.route("/")
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("blog/index.html", posts=posts)


@bp.route("/new", methods=["POST"])
def new_post():
    try:
        data = request.get_json()
        if not data or "basic_idea" not in data:
            return jsonify({"error": "basic_idea is required"}), 400
        temp_title = data["basic_idea"][:50] + "..."
        base_slug = slugify(temp_title)
        counter = 0
        slug = base_slug
        while Post.query.filter_by(slug=slug).first():
            counter += 1
            slug = f"{base_slug}-{counter}"
        post = Post()
        post.title = temp_title
        post.slug = slug
        post.published = False
        post.deleted = False
        post.content = ""
        db.session.add(post)
        db.session.flush()
        dev = PostDevelopment(post_id=post.id, basic_idea=data["basic_idea"])
        db.session.add(dev)
        db.session.commit()
        return jsonify(
            {"message": "Post created successfully", "slug": post.slug, "id": post.id}
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@bp.route("/<int:post_id>/", defaults={'view': 'preview'})
@bp.route("/<int:post_id>/<view>")
def post_view(post_id, view):
    post = Post.query.get_or_404(post_id)
    if view == 'develop':
        dev = PostDevelopment.query.filter_by(post_id=post_id).first()
        if not dev:
            dev = PostDevelopment(post_id=post_id)
            db.session.add(dev)
            db.session.commit()
        sections = (
            PostSection.query.filter_by(post_id=post_id)
            .order_by(PostSection.section_order)
            .all()
        )
        return render_template("blog/develop.html", post=post, dev=dev, sections=sections, active_view='develop', workflow_fields=WORKFLOW_FIELDS)
    elif view == 'json':
        post_json = {
            "id": post.id,
            "slug": post.slug,
            "title": post.title,
            "content": post.content,
            "published": post.published,
            "deleted": post.deleted,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        }
        return render_template("blog/json.html", post=post, post_json=post_json, active_view='json')
    elif view == 'preview':
        # For now, just render the develop template as a placeholder for preview
        dev = PostDevelopment.query.filter_by(post_id=post_id).first()
        sections = (
            PostSection.query.filter_by(post_id=post_id)
            .order_by(PostSection.section_order)
            .all()
        )
        return render_template("blog/develop.html", post=post, dev=dev, sections=sections, active_view='preview', workflow_fields=WORKFLOW_FIELDS)
    else:
        abort(404)


@bp.route('/develop/<int:post_id>')
def legacy_develop(post_id):
    return redirect(url_for('blog.post_view', post_id=post_id, view='develop'), code=301)


@bp.route('/<slug>')
def legacy_slug(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    return redirect(url_for('blog.post_view', post_id=post.id, view='preview'), code=301)


@bp.route("/api/v1/post/<int:post_id>/development", methods=["GET"])
def get_post_development(post_id):
    dev = PostDevelopment.query.filter_by(post_id=post_id).first_or_404()
    columns = [
        c.key
        for c in db.inspect(PostDevelopment).mapper.column_attrs
        if c.key not in ["id", "post_id"]
    ]
    return jsonify({c: getattr(dev, c) for c in columns})


@bp.route("/api/v1/post/<int:post_id>/development", methods=["POST"])
def update_post_development(post_id):
    dev = PostDevelopment.query.filter_by(post_id=post_id).first_or_404()
    data = request.get_json()
    columns = [
        c.key
        for c in db.inspect(PostDevelopment).mapper.column_attrs
        if c.key not in ["id", "post_id"]
    ]
    for field in columns:
        if field in data:
            setattr(dev, field, data[field])
    # Also update the parent Post's updated_at
    post = Post.query.get(post_id)
    if post:
        post.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "success", "updated_at": post.updated_at.isoformat() if post and post.updated_at else None})


@bp.route("/api/v1/post/<int:post_id>/sections", methods=["GET"])
def get_sections(post_id):
    sections = (
        PostSection.query.filter_by(post_id=post_id)
        .order_by(PostSection.section_order)
        .all()
    )
    columns = [
        c.key for c in db.inspect(PostSection).mapper.column_attrs if c.key != "post_id"
    ]
    return jsonify([{c: getattr(s, c) for c in columns} for s in sections])


@bp.route("/api/v1/post/<int:post_id>/sections", methods=["POST"])
def add_section(post_id):
    data = request.get_json() or {}
    section = PostSection(
        post_id=post_id,
        section_order=data.get("section_order", 0),
        section_heading=data.get("section_heading", ""),
    )
    db.session.add(section)
    db.session.commit()
    return jsonify({"id": section.id})


@bp.route("/api/v1/section/<int:section_id>", methods=["POST"])
def update_section(section_id):
    section = PostSection.query.get_or_404(section_id)
    data = request.get_json()
    columns = [
        c.key
        for c in db.inspect(PostSection).mapper.column_attrs
        if c.key not in ["id", "post_id"]
    ]
    for field in columns:
        if field in data:
            setattr(section, field, data[field])
    db.session.commit()
    return jsonify({"status": "success"})


@bp.route("/test_insert", methods=["GET"])
def test_insert():
    try:
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


@bp.route("/<slug>", methods=["GET"])
def get_post(slug):
    post = Post.query.filter_by(slug=slug, deleted=False).first()
    if not post:
        return jsonify({"error": "Post not found"}), 404
    return jsonify(
        {
            "id": post.id,
            "slug": post.slug,
            "title": post.title,
            "content": post.content,
            "published": post.published,
            "deleted": post.deleted,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        }
    )


@bp.route("/<slug>", methods=["PUT"])
def update_post(slug):
    post = Post.query.filter_by(slug=slug, deleted=False).first()
    if not post:
        return jsonify({"error": "Post not found"}), 404
    data = request.get_json() or {}
    if "title" in data:
        post.title = data["title"]
    if "content" in data:
        post.content = data["content"]
    db.session.commit()
    return jsonify(
        {
            "id": post.id,
            "slug": post.slug,
            "title": post.title,
            "content": post.content,
            "published": post.published,
            "deleted": post.deleted,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        }
    )


@bp.route("/<slug>", methods=["DELETE"])
def delete_post(slug):
    post = Post.query.filter_by(slug=slug, deleted=False).first()
    if not post:
        return jsonify({"error": "Post not found"}), 404
    post.deleted = True
    db.session.commit()
    return jsonify({"message": "Post deleted"})
