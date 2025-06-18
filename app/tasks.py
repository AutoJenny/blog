from app import celery, db
from app.models import Post
from app.blog.publishing import publish_post, PublishingError
from datetime import datetime, timedelta
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery.task
def check_scheduled_posts():
    """Check and publish any posts that are scheduled for the current time."""
    try:
        # Find posts that are scheduled and due for publishing
        scheduled_posts = Post.query.filter(
            Post.published == False,
            Post.published_at <= datetime.utcnow()
        ).all()
        
        for post in scheduled_posts:
            try:
                publish_post(post)
                logger.info(f"Successfully published scheduled post {post.id}: {post.title}")
            except PublishingError as e:
                logger.error(f"Failed to publish scheduled post {post.id}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error checking scheduled posts: {str(e)}")
        raise

@celery.task
def cleanup_old_drafts(days=30):
    """Mark old unpublished drafts as deleted."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_drafts = Post.query.filter(
            Post.published == False,
            Post.published_at == None,
            Post.updated_at < cutoff_date
        ).all()
        
        for draft in old_drafts:
            draft.status = 'deleted'
            logger.info(f"Marked old draft {draft.id} as deleted")
        db.session.commit()
    except Exception as e:
        logger.error(f"Error cleaning up old drafts: {str(e)}")
        db.session.rollback()
        raise 