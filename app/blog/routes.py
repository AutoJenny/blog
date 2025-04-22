from flask import render_template, flash, redirect, url_for, request, current_app
from app.blog import bp
from app.models import Post
from app import db

@bp.route('/create', methods=['GET', 'POST'])
def create():
    return render_template('blog/create.html', title='Create Post') 