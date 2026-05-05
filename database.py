"""
PaperPilot — Database Layer (SQLite + SQLAlchemy)
==================================================
Persistent storage for research sessions and reports.
Replaces the in-memory ResultCache for durable history.

Usage:
    from database import db, ResearchSession, init_db
"""

import os
import json
import logging
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger('paperpilot.db')

db = SQLAlchemy()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'paperpilot.db')


class ResearchSession(db.Model):
    """Stores each research session (both Lite and Pro)."""
    __tablename__ = 'research_sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    topic = db.Column(db.String(300), nullable=False)
    mode = db.Column(db.String(10), default='lite')  # 'lite' or 'pro'

    # Config (JSON string for Pro mode)
    config_json = db.Column(db.Text, default='{}')

    # Result (full report JSON)
    report_json = db.Column(db.Text, nullable=True)

    # Metadata
    total_sources = db.Column(db.Integer, default=0)
    elapsed_seconds = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_report(self, report_dict):
        self.report_json = json.dumps(report_dict, ensure_ascii=False)
        self.total_sources = report_dict.get('total_sources', 0)
        self.elapsed_seconds = report_dict.get('elapsed_seconds', 0)

    def get_report(self):
        if self.report_json:
            return json.loads(self.report_json)
        return None

    def to_history_dict(self):
        return {
            'session_id': self.session_id,
            'topic': self.topic,
            'mode': self.mode,
            'total_sources': self.total_sources,
            'elapsed_seconds': self.elapsed_seconds,
            'created_at': self.created_at.replace(tzinfo=timezone.utc).isoformat() if self.created_at else None,
        }


def init_db(app):
    """Initialize the database with the Flask app."""
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        logger.info(f"Database initialized at {DB_PATH}")


def save_session(session_id, topic, report, mode='lite', config=None):
    """Save a research session to the database."""
    try:
        existing = ResearchSession.query.filter_by(session_id=session_id).first()
        if existing:
            existing.set_report(report)
            existing.mode = mode
            if config:
                existing.config_json = json.dumps(config)
        else:
            session = ResearchSession(
                session_id=session_id,
                topic=topic,
                mode=mode,
                config_json=json.dumps(config or {}),
            )
            session.set_report(report)
            db.session.add(session)

        db.session.commit()
        logger.info(f"Saved session {session_id} for '{topic}' ({mode})")
    except Exception as e:
        db.session.rollback()
        logger.error(f"DB save_session failed, rolled back: {e}")
        raise


def get_session(session_id):
    """Retrieve a session by its ID."""
    session = ResearchSession.query.filter_by(session_id=session_id).first()
    if session:
        return session.get_report()
    return None


def get_history(limit=20):
    """Get recent research history."""
    sessions = (
        ResearchSession.query
        .order_by(ResearchSession.created_at.desc())
        .limit(limit)
        .all()
    )
    return [s.to_history_dict() for s in sessions]
