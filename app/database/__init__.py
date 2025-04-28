from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    url_for,
    request,
    current_app,
)
from app import db
from sqlalchemy import text
import subprocess
import os
import json
from pathlib import Path

bp = Blueprint("db", __name__, url_prefix="/db")

# Global replicator instance
replicator = None


@bp.route("/")
def index():
    return render_template("db/index.html")


@bp.route("/backup")
def backup():
    try:
        subprocess.run(["python", "scripts/db_backup.py"], check=True)
        flash("Database backup created successfully", "success")
    except subprocess.CalledProcessError:
        flash("Failed to create database backup", "error")
    return redirect(url_for("db.index"))


@bp.route("/restore")
def restore():
    return render_template("db/restore.html")


@bp.route("/vacuum")
def vacuum():
    try:
        db.session.execute(text("VACUUM"))
        db.session.commit()
        flash("Database vacuum completed successfully", "success")
    except Exception as e:
        flash(f"Failed to vacuum database: {str(e)}", "error")
    return redirect(url_for("db.index"))


@bp.route("/check_integrity")
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
def stats():
    return render_template("db/stats.html")


@bp.route("/logs")
def logs():
    return render_template("db/logs.html")


@bp.route("/migrations")
def migrations():
    return render_template("db/migrations.html")


@bp.route("/replication")
def replication():
    status_file = Path(current_app.instance_path) / "replication_status.json"
    status = {}
    config = {"check_interval": 60}  # Default config

    if status_file.exists():
        try:
            with open(status_file) as f:
                status = json.load(f)
        except json.JSONDecodeError:
            flash("Error reading replication status", "error")

    config_file = Path(current_app.instance_path) / "replication_config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
        except json.JSONDecodeError:
            flash("Error reading replication configuration", "error")

    return render_template("db/replication.html", status=status, config=config)


@bp.route("/replication/start")
def start_replication():
    global replicator
    try:
        if not replicator:
            from scripts.db_replication import DatabaseReplicator

            primary_db = Path(current_app.instance_path) / "blog.db"
            replica_db = Path(current_app.instance_path) / "blog.replica.db"
            replicator = DatabaseReplicator(primary_db, replica_db)
            replicator.start()
            flash("Replication started successfully", "success")
        else:
            flash("Replication is already running", "warning")
    except Exception as e:
        flash(f"Failed to start replication: {str(e)}", "error")
    return redirect(url_for("db.replication"))


@bp.route("/replication/stop")
def stop_replication():
    global replicator
    try:
        if replicator:
            replicator.stop()
            replicator = None
            flash("Replication stopped successfully", "success")
        else:
            flash("Replication is not running", "warning")
    except Exception as e:
        flash(f"Failed to stop replication: {str(e)}", "error")
    return redirect(url_for("db.replication"))


@bp.route("/replication/force")
def force_sync():
    global replicator
    try:
        if replicator:
            replicator._sync_databases()
            flash("Force sync completed successfully", "success")
        else:
            flash("Replication is not running", "warning")
    except Exception as e:
        flash(f"Force sync failed: {str(e)}", "error")
    return redirect(url_for("db.replication"))


@bp.route("/replication/config", methods=["POST"])
def update_replication_config():
    try:
        check_interval = int(request.form.get("check_interval", 60))
        check_interval = max(10, min(3600, check_interval))  # Clamp between 10s and 1h

        config = {"check_interval": check_interval}
        config_file = Path(current_app.instance_path) / "replication_config.json"

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        if replicator:
            replicator.check_interval = check_interval

        flash("Configuration updated successfully", "success")
    except Exception as e:
        flash(f"Failed to update configuration: {str(e)}", "error")

    return redirect(url_for("db.replication"))
