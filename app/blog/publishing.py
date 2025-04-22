from datetime import datetime
from flask import current_app
from app.models import Post, WorkflowStage, WorkflowStatus, WorkflowStatusHistory
from app import db
from sqlalchemy.exc import SQLAlchemyError
from app.blog.syndication import syndicate_post, remove_syndicated_post, SyndicationError

class PublishingError(Exception):
    """Custom exception for publishing-related errors."""
    pass

def validate_for_publishing(post):
    """
    Validate that a post is ready for publishing.
    
    Args:
        post (Post): The post to validate
        
    Returns:
        tuple: (bool, list) - (is_valid, list of validation errors)
    """
    errors = []
    
    # Required fields
    if not post.title:
        errors.append("Post title is required")
    if not post.content:
        errors.append("Post content is required")
    if not post.summary:
        errors.append("Post summary is required")
    if not post.categories:
        errors.append("At least one category is required")
    if not post.header_image:
        errors.append("Header image is required")
        
    # Workflow validation
    if not post.workflow_status:
        errors.append("Post must have a workflow status")
    elif post.workflow_status.current_stage != WorkflowStage.VALIDATION:
        errors.append(f"Post must be in VALIDATION stage (currently in {post.workflow_status.current_stage.value})")
        
    # Content validation
    if len(post.title) > 200:
        errors.append("Title is too long (max 200 characters)")
    if len(post.summary) > 500:
        errors.append("Summary is too long (max 500 characters)")
        
    return (len(errors) == 0, errors)

def schedule_post_publishing(post, publish_at):
    """
    Schedule a post to be published at a specific time.
    
    Args:
        post (Post): The post to schedule
        publish_at (datetime): When to publish the post
        
    Raises:
        PublishingError: If the post cannot be scheduled
    """
    if publish_at <= datetime.utcnow():
        raise PublishingError("Scheduled time must be in the future")
        
    is_valid, errors = validate_for_publishing(post)
    if not is_valid:
        raise PublishingError(f"Post validation failed: {', '.join(errors)}")
        
    try:
        # Update post
        post.published_at = publish_at
        
        # Update workflow status
        if post.workflow_status.current_stage != WorkflowStage.PUBLISHING:
            history = WorkflowStatusHistory(
                workflow_status_id=post.workflow_status.id,
                from_stage=post.workflow_status.current_stage,
                to_stage=WorkflowStage.PUBLISHING,
                user_id=post.author_id,
                notes=f"Scheduled for publishing at {publish_at.isoformat()}"
            )
            post.workflow_status.current_stage = WorkflowStage.PUBLISHING
            db.session.add(history)
            
        db.session.commit()
        current_app.logger.info(f"Post {post.id} scheduled for publishing at {publish_at.isoformat()}")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        raise PublishingError(f"Failed to schedule post: {str(e)}")

def publish_post(post):
    """
    Immediately publish a post.
    
    Args:
        post (Post): The post to publish
        
    Raises:
        PublishingError: If the post cannot be published
    """
    is_valid, errors = validate_for_publishing(post)
    if not is_valid:
        raise PublishingError(f"Post validation failed: {', '.join(errors)}")
        
    try:
        # Update post
        post.published = True
        post.published_at = datetime.utcnow()
        
        # Update workflow status
        if post.workflow_status.current_stage != WorkflowStage.PUBLISHING:
            history = WorkflowStatusHistory(
                workflow_status_id=post.workflow_status.id,
                from_stage=post.workflow_status.current_stage,
                to_stage=WorkflowStage.PUBLISHING,
                user_id=post.author_id,
                notes="Post published"
            )
            post.workflow_status.current_stage = WorkflowStage.PUBLISHING
            db.session.add(history)
            
        # Commit changes before syndication
        db.session.commit()
        
        # Attempt to syndicate to clan.com
        try:
            syndicate_post(post)
        except SyndicationError as e:
            current_app.logger.error(f"Failed to syndicate post {post.id}: {str(e)}")
            # Don't rollback publishing if syndication fails
            
        current_app.logger.info(f"Post {post.id} published successfully")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        raise PublishingError(f"Failed to publish post: {str(e)}")

def unpublish_post(post):
    """
    Unpublish a post (revert to draft).
    
    Args:
        post (Post): The post to unpublish
        
    Raises:
        PublishingError: If the post cannot be unpublished
    """
    if not post.published:
        raise PublishingError("Post is not currently published")
        
    try:
        # Remove from clan.com first
        if post.clan_com_post_id:
            try:
                remove_syndicated_post(post)
            except SyndicationError as e:
                current_app.logger.error(f"Failed to remove syndicated post {post.id}: {str(e)}")
                # Continue with unpublishing even if syndication removal fails
        
        # Update post
        post.published = False
        post.published_at = None
        
        # Update workflow status
        history = WorkflowStatusHistory(
            workflow_status_id=post.workflow_status.id,
            from_stage=post.workflow_status.current_stage,
            to_stage=WorkflowStage.VALIDATION,
            user_id=post.author_id,
            notes="Post unpublished"
        )
        post.workflow_status.current_stage = WorkflowStage.VALIDATION
        db.session.add(history)
            
        db.session.commit()
        current_app.logger.info(f"Post {post.id} unpublished successfully")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        raise PublishingError(f"Failed to unpublish post: {str(e)}")

def get_scheduled_posts():
    """
    Get all posts scheduled for future publishing.
    
    Returns:
        list: List of Post objects scheduled for future publishing
    """
    return Post.query.filter(
        Post.published == False,
        Post.published_at > datetime.utcnow()
    ).order_by(Post.published_at).all()

def get_published_posts():
    """
    Get all currently published posts.
    
    Returns:
        list: List of published Post objects
    """
    return Post.query.filter_by(
        published=True,
        deleted=False
    ).order_by(Post.published_at.desc()).all() 