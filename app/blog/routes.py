from flask import render_template, flash, redirect, url_for, request, current_app
from app.blog import bp
from app.models import Post, Category
from app import db

@bp.route('/create', methods=['GET', 'POST'])
def create():
    return render_template('blog/create.html', title='Create Post')

@bp.route('/latest')
def latest():
    """Display latest blog posts."""
    posts = Post.query.filter_by(
        published=True,
        deleted=False
    ).order_by(Post.created_at.desc()).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=10,
        error_out=False
    )
    return render_template('blog/latest.html', title='Latest Posts', posts=posts)

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