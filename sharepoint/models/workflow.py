from datetime import datetime, timezone
from models import db


class CheckOut(db.Model):
    __tablename__ = 'checkouts'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    checked_out_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    checked_out_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    checked_in_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', foreign_keys=[checked_out_by])


class SignOff(db.Model):
    __tablename__ = 'signoffs'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    sign_off_type = db.Column(db.String(20), nullable=False)  # preparer, reviewer
    signed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    signed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    cleared_at = db.Column(db.DateTime, nullable=True)
    cleared_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    signer = db.relationship('User', foreign_keys=[signed_by])
    clearer = db.relationship('User', foreign_keys=[cleared_by])


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    creator = db.relationship('User', foreign_keys=[created_by])
    resolver = db.relationship('User', foreign_keys=[resolved_by])


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    binder_id = db.Column(db.Integer, db.ForeignKey('binders.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50), default='')
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id])
