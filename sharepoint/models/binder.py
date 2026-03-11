from datetime import datetime, timezone
from models import db


class Binder(db.Model):
    __tablename__ = 'binders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    client_name = db.Column(db.String(200), nullable=False)
    engagement_type = db.Column(db.String(50), nullable=False, default='audit')  # audit, tax, review, compilation, other
    period_end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')  # active, archived, template
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    creator = db.relationship('User', foreign_keys=[created_by])
    access_list = db.relationship('BinderAccess', backref='binder', cascade='all, delete-orphan')
    folders = db.relationship('Folder', backref='binder', cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='binder', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Binder {self.name}>'


class BinderAccess(db.Model):
    __tablename__ = 'binder_access'

    id = db.Column(db.Integer, primary_key=True)
    binder_id = db.Column(db.Integer, db.ForeignKey('binders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    access_level = db.Column(db.String(20), nullable=False, default='viewer')  # owner, editor, viewer

    user = db.relationship('User')

    __table_args__ = (db.UniqueConstraint('binder_id', 'user_id'),)


class Folder(db.Model):
    __tablename__ = 'folders'

    id = db.Column(db.Integer, primary_key=True)
    binder_id = db.Column(db.Integer, db.ForeignKey('binders.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    index_number = db.Column(db.String(20), default='')  # e.g. "A", "B-1"
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    children = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]),
                               order_by='Folder.sort_order')
    documents = db.relationship('Document', backref='folder')

    def __repr__(self):
        return f'<Folder {self.index_number} - {self.name}>'
