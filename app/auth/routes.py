from flask import render_template, flash, redirect, url_for, request
from app.auth import bp
from flask_login import login_user, logout_user, current_user

@bp.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('auth/login.html', title='Sign In')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index')) 