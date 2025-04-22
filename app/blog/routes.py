from flask import render_template, flash, redirect, url_for, request, current_app, jsonify, abort
from app.blog import bp
from app.models import Post, Category, Tag, WorkflowStage, WorkflowStatus, WorkflowStatusHistory, Image
from app import db
from app.blog.publishing import (
    publish_post, unpublish_post, schedule_post_publishing,
    get_scheduled_posts, get_published_posts, PublishingError
)
from app.blog.forms import PostForm
# from flask_login import login_required, current_user  # Temporarily disabled
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError
import re

# Temporary development user context
class DevUser:
    id = 1
    is_authenticated = True
    is_admin = True

current_user = DevUser()  # Temporary development user

def slugify(text):
    """Convert text to a URL-friendly slug."""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces with hyphens
    text = re.sub(r'[\s]+', '-', text)
    # Remove special characters
    text = re.sub(r'[^\w\-]', '', text)
    # Remove duplicate hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text

@bp.route('/')
@bp.route('/latest')
def latest():
    try:
        page = request.args.get('page', 1, type=int)
        posts = Post.query.order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=10,
            error_out=False
        )
        return render_template('blog/latest.html', posts=posts)
    except Exception as e:
        current_app.logger.error(f"Error fetching posts: {str(e)}")
        flash('An error occurred while loading posts.', 'error')
        return render_template('blog/latest.html', posts=[])

@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create a new blog post."""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            # Create workflow status
            workflow_status = WorkflowStatus(
                current_stage=WorkflowStage.CONCEPTUALIZATION
            )
            db.session.add(workflow_status)
            
            # Create new post with basic fields
            post = Post(
                title=title,
                slug=slugify(title),  # Generate slug from title
                content=request.form.get('content'),
                summary=request.form.get('summary'),
                published=False,
                author_id=current_user.id,  # Set the author_id
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                workflow_status=workflow_status  # Link the workflow status
            )
            
            # Create initial workflow history - use the same stage for from/to since this is initialization
            history = WorkflowStatusHistory(
                workflow_status=workflow_status,
                from_stage=WorkflowStage.CONCEPTUALIZATION,  # Initialize with the same stage
                to_stage=WorkflowStage.CONCEPTUALIZATION,
                user_id=current_user.id,
                notes="Post created"
            )
            db.session.add(history)
            
            db.session.add(post)
            db.session.commit()
            
            flash('Post created successfully!', 'success')
            return redirect(url_for('blog.edit', post_id=post.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating post: {str(e)}")
            flash('An error occurred while creating the post. Please try again.', 'error')
            
    return render_template('blog/create.html')

@bp.route('/categories')
def categories():
    """Display all blog categories."""
    categories = Category.query.order_by(Category.name).all()
    return render_template('blog/categories.html', title='Categories', categories=categories)

@bp.route('/category/<string:category>')
def category(category):
    """Display posts for a specific category."""
    category_obj = Category.query.filter_by(slug=category).first_or_404()
    posts = Post.query.filter_by(
        category_id=category_obj.id,
        published=True,
        deleted=False
    ).order_by(Post.created_at.desc()).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=10,
        error_out=False
    )
    return render_template('blog/category.html', title=f'Category: {category_obj.name}', 
                         category=category_obj, posts=posts)

@bp.route('/post/<int:post_id>/publish', methods=['POST'])
def publish(post_id):
    """Publish a post immediately."""
    post = Post.query.get_or_404(post_id)
    
    try:
        publish_post(post)
        flash('Post published successfully!', 'success')
        return jsonify({'status': 'success', 'message': 'Post published successfully'})
    except PublishingError as e:
        flash(str(e), 'error')
        return jsonify({'status': 'error', 'message': str(e)}), 400

@bp.route('/post/<int:post_id>/schedule', methods=['POST'])
def schedule(post_id):
    """Schedule a post for future publishing."""
    post = Post.query.get_or_404(post_id)
    
    try:
        publish_at = datetime.fromisoformat(request.form['publish_at'])
        schedule_post_publishing(post, publish_at)
        flash('Post scheduled for publishing!', 'success')
        return jsonify({
            'status': 'success',
            'message': f'Post scheduled for publishing at {publish_at.isoformat()}'
        })
    except (ValueError, KeyError):
        flash('Invalid publishing date format', 'error')
        return jsonify({
            'status': 'error',
            'message': 'Invalid publishing date format'
        }), 400
    except PublishingError as e:
        flash(str(e), 'error')
        return jsonify({'status': 'error', 'message': str(e)}), 400

@bp.route('/post/<int:post_id>/unpublish', methods=['POST'])
def unpublish(post_id):
    """Unpublish a post (revert to draft)."""
    post = Post.query.get_or_404(post_id)
    
    try:
        unpublish_post(post)
        flash('Post unpublished successfully!', 'success')
        return jsonify({'status': 'success', 'message': 'Post unpublished successfully'})
    except PublishingError as e:
        flash(str(e), 'error')
        return jsonify({'status': 'error', 'message': str(e)}), 400

@bp.route('/scheduled')
def scheduled_posts():
    """View all scheduled posts."""
    posts = get_scheduled_posts()
    return render_template('blog/scheduled.html', title='Scheduled Posts', posts=posts)

@bp.route('/published')
def published_posts():
    """View all published posts."""
    posts = get_published_posts()
    return render_template('blog/published.html', title='Published Posts', posts=posts)

@bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit(post_id):
    """Edit an existing blog post."""
    post = Post.query.get_or_404(post_id)
    
    # Check if user has permission to edit
    if post.author_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this post.', 'error')
        return redirect(url_for('blog.latest'))
    
    # Ensure post has a workflow status
    if not post.workflow_status:
        workflow_status = WorkflowStatus(
            current_stage=WorkflowStage.CONCEPTUALIZATION
        )
        db.session.add(workflow_status)
        
        # Create initial workflow history - use the same stage for from/to since this is initialization
        history = WorkflowStatusHistory(
            workflow_status=workflow_status,
            from_stage=WorkflowStage.CONCEPTUALIZATION,  # Initialize with the same stage
            to_stage=WorkflowStage.CONCEPTUALIZATION,
            user_id=current_user.id,
            notes="Workflow status initialized for existing post"
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
    if request.method == 'GET':
        form.categories.data = [c.id for c in post.categories]
        form.tags.data = ', '.join(tag.name for tag in post.tags)
    
    if form.validate_on_submit():
        try:
            # Update basic fields
            form.populate_obj(post)
            
            # Handle categories
            post.categories = []
            categories = Category.query.filter(Category.id.in_(form.categories.data)).all()
            post.categories.extend(categories)
            
            # Handle tags
            post.tags = []
            if form.tags.data:
                tag_names = [t.strip() for t in form.tags.data.split(',')]
                for tag_name in tag_names:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name, slug=tag_name.lower().replace(' ', '-'))
                        db.session.add(tag)
                    post.tags.append(tag)
            
            # Handle header image
            if form.header_image.data:
                filename = secure_filename(form.header_image.data.filename)
                file_path = os.path.join('uploads', 'headers', filename)
                
                # Ensure upload directory exists
                os.makedirs(os.path.join(current_app.static_folder, 'uploads', 'headers'), exist_ok=True)
                
                # Save file
                form.header_image.data.save(os.path.join(current_app.static_folder, file_path))
                
                # Create image record
                image = Image(
                    path=file_path,
                    alt_text=form.title.data,
                    uploaded_by=current_user.id
                )
                db.session.add(image)
                post.header_image = image
            
            # Update workflow status if needed and exists
            if post.workflow_status and post.workflow_status.current_stage == WorkflowStage.CONCEPTUALIZATION:
                history = WorkflowStatusHistory(
                    workflow_status=post.workflow_status,
                    from_stage=WorkflowStage.CONCEPTUALIZATION,
                    to_stage=WorkflowStage.AUTHORING,
                    user_id=current_user.id,
                    notes="Post content updated"
                )
                post.workflow_status.current_stage = WorkflowStage.AUTHORING
                db.session.add(history)
            
            db.session.commit()
            flash('Post updated successfully!', 'success')
            
            if 'save_draft' in request.form:
                return redirect(url_for('blog.edit', post_id=post.id))
            return redirect(url_for('blog.post', post_id=post.id))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating post: {str(e)}")
            flash('An error occurred while updating the post. Please try again.', 'error')
    
    return render_template('blog/edit.html', title='Edit Post', form=form, post=post)

@bp.route('/post/<int:post_id>')
def post(post_id):
    """Display a single blog post."""
    post = Post.query.get_or_404(post_id)
    
    # If post is not published, only author and admin can view it
    if not post.published:
        if not current_user.is_authenticated or \
           (post.author_id != current_user.id and not current_user.is_admin):
            flash('This post is not published yet.', 'error')
            return redirect(url_for('blog.latest'))
    
    # If post is deleted, only admin can view it
    if post.deleted and not (current_user.is_authenticated and current_user.is_admin):
        abort(404)
    
    return render_template('blog/post.html', title=post.title, post=post)

@bp.route('/post/<int:post_id>/delete', methods=['POST'])
def delete(post_id):
    """Delete a blog post (soft delete)."""
    post = Post.query.get_or_404(post_id)
    
    # Only admin can delete posts
    if not current_user.is_admin:
        flash('You do not have permission to delete posts.', 'error')
        return jsonify({'status': 'error', 'message': 'Permission denied'}), 403
    
    try:
        # Soft delete
        post.deleted = True
        post.deleted_at = datetime.utcnow()
        post.deleted_by = current_user.id
        
        # If published, unpublish first
        if post.published:
            try:
                unpublish_post(post)
            except PublishingError as e:
                current_app.logger.error(f"Error unpublishing deleted post {post.id}: {str(e)}")
        
        db.session.commit()
        flash('Post deleted successfully.', 'success')
        return jsonify({'status': 'success', 'message': 'Post deleted successfully'})
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting post {post.id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'An error occurred while deleting the post'}), 500 