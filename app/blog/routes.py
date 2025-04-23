from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    current_app,
    jsonify,
    abort,
)
from app.blog import bp
from app.models import (
    Post,
    Category,
    Tag,
    WorkflowStage,
    WorkflowStatus,
    WorkflowStatusHistory,
    Image,
    PostSection,
)
from app import db
from app.blog.publishing import (
    publish_post,
    unpublish_post,
    schedule_post_publishing,
    get_scheduled_posts,
    get_published_posts,
    PublishingError,
)
from app.blog.forms import PostForm
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError
import re
import json


def slugify(text):
    """Convert text to a URL-friendly slug."""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces with hyphens
    text = re.sub(r"[\s]+", "-", text)
    # Remove special characters
    text = re.sub(r"[^\w\-]", "", text)
    # Remove duplicate hyphens
    text = re.sub(r"-+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")
    return text


@bp.route("/")
@bp.route("/latest")
def latest():
    try:
        page = request.args.get("page", 1, type=int)
        posts = Post.query.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        return render_template("blog/latest.html", posts=posts)
    except Exception as e:
        current_app.logger.error(f"Error fetching posts: {str(e)}")
        flash("An error occurred while loading posts.", "error")
        return render_template("blog/latest.html", posts=[])


@bp.route("/create", methods=["GET", "POST"])
def create():
    """Create a new blog post."""
    if request.method == "POST":
        try:
            title = request.form.get("title")
            # Create workflow status
            workflow_status = WorkflowStatus(
                current_stage=WorkflowStage.CONCEPTUALIZATION
            )
            db.session.add(workflow_status)

            # Create new post with basic fields
            post = Post(
                title=title,
                slug=slugify(title),  # Generate slug from title
                content=request.form.get("content"),
                summary=request.form.get("summary"),
                published=False,
                author_id=1,  # Default author ID
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                workflow_status=workflow_status,  # Link the workflow status
            )

            # Create initial workflow history
            history = WorkflowStatusHistory(
                workflow_status=workflow_status,
                from_stage=WorkflowStage.CONCEPTUALIZATION,
                to_stage=WorkflowStage.CONCEPTUALIZATION,
                user_id=1,  # Default user ID
                notes="Post created",
            )
            db.session.add(history)

            db.session.add(post)
            db.session.commit()

            flash("Post created successfully!", "success")
            return redirect(url_for("blog.edit", slug=post.slug))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating post: {str(e)}")
            flash(
                "An error occurred while creating the post. Please try again.", "error"
            )

    return render_template("blog/create.html")


@bp.route("/categories")
def categories():
    """Display all blog categories."""
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "blog/categories.html", title="Categories", categories=categories
    )


@bp.route("/category/<string:category>")
def category(category):
    """Display posts for a specific category."""
    category_obj = Category.query.filter_by(slug=category).first_or_404()
    posts = (
        Post.query.filter_by(category_id=category_obj.id, published=True, deleted=False)
        .order_by(Post.created_at.desc())
        .paginate(
            page=request.args.get("page", 1, type=int), per_page=10, error_out=False
        )
    )
    return render_template(
        "blog/category.html",
        title=f"Category: {category_obj.name}",
        category=category_obj,
        posts=posts,
    )


@bp.route("/post/<string:slug>")
def post(slug):
    """Display a blog post."""
    post = Post.query.filter_by(slug=slug).first_or_404()
    return render_template("blog/post.html", post=post, active_tab="preview")


@bp.route("/post/<string:slug>/edit", methods=["GET", "POST"])
def edit(slug):
    """Edit an existing blog post."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    # Ensure post has a workflow status
    if not post.workflow_status:
        workflow_status = WorkflowStatus(current_stage=WorkflowStage.CONCEPTUALIZATION)
        db.session.add(workflow_status)

        # Create initial workflow history
        history = WorkflowStatusHistory(
            workflow_status=workflow_status,
            from_stage=WorkflowStage.CONCEPTUALIZATION,
            to_stage=WorkflowStage.CONCEPTUALIZATION,
            user_id=1,  # Default user ID
            notes="Workflow status initialized for existing post",
        )
        db.session.add(history)

        post.workflow_status = workflow_status
        db.session.commit()

    form = PostForm(obj=post)

    # Populate category choices
    form.categories.choices = [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]

    # Pre-select current categories
    if request.method == "GET":
        form.categories.data = [c.id for c in post.categories]
        form.tags.data = ", ".join(tag.name for tag in post.tags)
        if post.seo_metadata:
            form.seo_title.data = post.seo_metadata.get("title", "")
            form.seo_description.data = post.seo_metadata.get("description", "")
        if post.header_image:
            form.header_image_alt.data = post.header_image.alt_text

    if form.validate_on_submit():
        try:
            # Update basic fields
            post.title = form.title.data
            post.content = form.content.data
            post.summary = form.summary.data
            post.concept = form.concept.data

            # Handle categories
            post.categories = Category.query.filter(
                Category.id.in_(form.categories.data)
            ).all()

            # Handle tags
            if form.tags.data:
                tag_names = [t.strip() for t in form.tags.data.split(",")]
                post.tags = []
                for tag_name in tag_names:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    post.tags.append(tag)

            # Handle header image
            if form.header_image.data:
                if post.header_image:
                    # Delete old image file
                    old_path = os.path.join(
                        current_app.root_path, "static", post.header_image.path
                    )
                    if os.path.exists(old_path):
                        os.remove(old_path)

                filename = secure_filename(form.header_image.data.filename)
                filepath = os.path.join("uploads", filename)
                full_path = os.path.join(current_app.root_path, "static", filepath)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                form.header_image.data.save(full_path)

                if post.header_image:
                    post.header_image.path = filepath
                    post.header_image.alt_text = form.header_image_alt.data
                else:
                    image = Image(
                        path=filepath,
                        alt_text=form.header_image_alt.data,
                        caption=post.title,
                    )
                    db.session.add(image)
                    post.header_image = image
            elif form.header_image_alt.data and post.header_image:
                post.header_image.alt_text = form.header_image_alt.data

            # Update SEO metadata
            post.seo_metadata = {
                "title": form.seo_title.data,
                "description": form.seo_description.data,
            }

            # Handle workflow stage transitions
            current_stage = post.workflow_status.current_stage

            if "next_stage" in request.form and request.form["next_stage"] == "next":
                # Validate current stage
                if not form.validate_for_stage(current_stage):
                    flash(
                        f"Please complete all required fields for the {current_stage.value} stage.",
                        "error",
                    )
                    return render_template(
                        "blog/edit.html", title="Edit Post", form=form, post=post
                    )

                # Get next stage
                stages = list(WorkflowStage)
                current_index = stages.index(current_stage)
                if current_index < len(stages) - 1:
                    next_stage = stages[current_index + 1]

                    # Create workflow history
                    history = WorkflowStatusHistory(
                        workflow_status=post.workflow_status,
                        from_stage=current_stage,
                        to_stage=next_stage,
                        user_id=1,  # Default user ID
                        notes=f"Advanced from {current_stage.value} to {next_stage.value}",
                    )
                    db.session.add(history)

                    # Update current stage
                    post.workflow_status.current_stage = next_stage

            # Handle publishing
            if "publish" in request.form and request.form["publish"] == "true":
                if form.schedule_publish.data:
                    try:
                        publish_at = datetime.fromisoformat(form.schedule_publish.data)
                        schedule_post_publishing(post, publish_at)
                        flash("Post scheduled for publishing!", "success")
                    except (ValueError, PublishingError) as e:
                        flash(str(e), "error")
                else:
                    try:
                        publish_post(post)
                        flash("Post published successfully!", "success")
                    except PublishingError as e:
                        flash(str(e), "error")

            post.updated_at = datetime.utcnow()
            db.session.commit()

            if "save_draft" in request.form:
                flash("Draft saved successfully!", "success")
                return redirect(url_for("blog.edit", slug=post.slug))

            flash("Post updated successfully!", "success")
            return redirect(url_for("blog.post", slug=post.slug))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating post: {str(e)}")
            flash(
                "An error occurred while updating the post. Please try again.", "error"
            )

    return render_template(
        "blog/edit.html", title="Edit Post", form=form, post=post, active_tab="edit"
    )


@bp.route("/post/<string:slug>/code")
def post_code(slug):
    """Display the code/data view of a blog post."""
    post = Post.query.filter_by(slug=slug).first_or_404()
    return render_template("blog/post_code.html", post=post, active_tab="code")


@bp.route("/post/<string:slug>/delete", methods=["POST"])
def delete(slug):
    """Delete a blog post (soft delete)."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    try:
        # Soft delete
        post.deleted = True
        post.deleted_at = datetime.utcnow()
        post.deleted_by = 1  # Default user ID

        # If published, unpublish first
        if post.published:
            try:
                unpublish_post(post)
            except PublishingError as e:
                current_app.logger.error(
                    f"Error unpublishing deleted post {post.id}: {str(e)}"
                )

        db.session.commit()
        flash("Post deleted successfully.", "success")
        return jsonify({"status": "success", "message": "Post deleted successfully"})

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting post {post.id}: {str(e)}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An error occurred while deleting the post",
                }
            ),
            500,
        )


@bp.route("/section/<int:section_id>/sql", methods=["GET"])
def edit_section_sql(section_id):
    """Edit a section using direct SQL."""
    section = PostSection.query.get_or_404(section_id)
    return render_template("blog/section_sql.html", section=section)


@bp.route("/section/<int:section_id>/sql/update", methods=["POST"])
def update_section_sql(section_id):
    """Execute SQL query to update a section."""
    section = PostSection.query.get_or_404(section_id)

    sql_query = request.form.get("sql_query")
    if not sql_query:
        flash("SQL query is required.", "error")
        return redirect(url_for("blog.edit_section_sql", section_id=section_id))

    try:
        # Execute the SQL query
        db.session.execute(db.text(sql_query))
        db.session.commit()
        flash("SQL query executed successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error executing SQL query: {str(e)}", "error")
        current_app.logger.error(f"SQL Error for section {section_id}: {str(e)}")
        return redirect(url_for("blog.edit_section_sql", section_id=section_id))

    return redirect(url_for("blog.edit", slug=section.post.slug))


@bp.route("/post/<string:slug>/publish", methods=["POST"])
def publish(slug):
    """Publish a post immediately."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    try:
        publish_post(post)
        flash("Post published successfully!", "success")
        return jsonify({"status": "success", "message": "Post published successfully"})
    except PublishingError as e:
        flash(str(e), "error")
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/post/<string:slug>/schedule", methods=["POST"])
def schedule(slug):
    """Schedule a post for future publishing."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    try:
        publish_at = datetime.fromisoformat(request.form["publish_at"])
        schedule_post_publishing(post, publish_at)
        flash("Post scheduled for publishing!", "success")
        return jsonify(
            {
                "status": "success",
                "message": f"Post scheduled for publishing at {publish_at.isoformat()}",
            }
        )
    except (ValueError, KeyError):
        flash("Invalid publishing date format", "error")
        return (
            jsonify({"status": "error", "message": "Invalid publishing date format"}),
            400,
        )
    except PublishingError as e:
        flash(str(e), "error")
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/post/<string:slug>/unpublish", methods=["POST"])
def unpublish(slug):
    """Unpublish a post (revert to draft)."""
    post = Post.query.filter_by(slug=slug).first_or_404()

    try:
        unpublish_post(post)
        flash("Post unpublished successfully!", "success")
        return jsonify(
            {"status": "success", "message": "Post unpublished successfully"}
        )
    except PublishingError as e:
        flash(str(e), "error")
        return jsonify({"status": "error", "message": str(e)}), 400


@bp.route("/scheduled")
def scheduled_posts():
    """View all scheduled posts."""
    posts = get_scheduled_posts()
    return render_template("blog/scheduled.html", title="Scheduled Posts", posts=posts)


@bp.route("/published")
def published_posts():
    """View all published posts."""
    posts = get_published_posts()
    return render_template("blog/published.html", title="Published Posts", posts=posts)


@bp.route("/section/<int:section_id>/edit", methods=["GET", "POST"])
def edit_section(section_id):
    """Edit a section."""
    section = PostSection.query.get_or_404(section_id)
    if request.method == "POST":
        section.title = request.form.get("title", section.title)
        section.subtitle = request.form.get("subtitle", section.subtitle)
        section.content = request.form.get("content", section.content)
        section.content_type = request.form.get("content_type", section.content_type)
        section.position = int(request.form.get("position", section.position))
        section.video_url = request.form.get("video_url") or None
        section.audio_url = request.form.get("audio_url") or None
        section.duration = int(request.form.get("duration", 0)) or None
        section.keywords = request.form.get("keywords") or None

        # Handle JSON fields
        try:
            if social_snippets := request.form.get("social_media_snippets"):
                section.social_media_snippets = json.loads(social_snippets)
            if metadata := request.form.get("section_metadata"):
                section.section_metadata = json.loads(metadata)
        except json.JSONDecodeError as e:
            flash(f"Error parsing JSON: {str(e)}", "error")
            return render_template("blog/edit_section.html", section=section)

        try:
            db.session.commit()
            flash("Section updated successfully.", "success")
            return redirect(url_for("blog.edit", slug=section.post.slug))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating section: {str(e)}", "error")
            current_app.logger.error(f"Error updating section {section_id}: {str(e)}")

    return render_template("blog/edit_section.html", section=section)


@bp.route("/tag/<string:tag>")
def tag(tag):
    """Display posts with a specific tag."""
    tag_obj = Tag.query.filter_by(slug=tag).first_or_404()
    posts = (
        Post.query.join(Post.tags)
        .filter(Tag.id == tag_obj.id)
        .order_by(Post.published_at.desc())
        .all()
    )
    return render_template("blog/tag.html", tag=tag_obj, posts=posts)
