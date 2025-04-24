from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required
from app import db
from sqlalchemy import text
import subprocess
import os

bp = Blueprint("db", __name__, url_prefix="/db")


@bp.route("/")
@login_required
def index():
    return render_template("db/index.html")


@bp.route("/backup")
@login_required
def backup():
    try:
        subprocess.run(["python", "scripts/db_backup.py"], check=True)
        flash("Database backup created successfully", "success")
    except subprocess.CalledProcessError:
        flash("Failed to create database backup", "error")
    return redirect(url_for("db.index"))


@bp.route("/restore")
@login_required
def restore():
    return render_template("db/restore.html")


@bp.route("/vacuum")
@login_required
def vacuum():
    try:
        db.session.execute(text("VACUUM"))
        db.session.commit()
        flash("Database vacuum completed successfully", "success")
    except Exception as e:
        flash(f"Failed to vacuum database: {str(e)}", "error")
    return redirect(url_for("db.index"))


@bp.route("/check_integrity")
@login_required
def check_integrity():
    try:
        result = db.session.execute(text("PRAGMA integrity_check")).scalar()
        if result == "ok":
            flash("Database integrity check passed", "success")
        else:
            flash(f"Database integrity check failed: {result}", "error")
    except Exception as e:
        flash(f"Failed to check database integrity: {str(e)}", "error")
    return redirect(url_for("db.index"))


@bp.route("/stats")
@login_required
def stats():
    return render_template("db/stats.html")


@bp.route("/logs")
@login_required
def logs():
    return render_template("db/logs.html")


@bp.route("/migrations")
@login_required
def migrations():
    return render_template("db/migrations.html")


@bp.route("/replication")
@login_required
def replication():
    return render_template("db/replication.html")
