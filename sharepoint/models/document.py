from datetime import datetime, timezone
from models import db


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=False)
    binder_id = db.Column(db.Integer, db.ForeignKey('binders.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), default='')
    current_version = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='active')  # active, deleted
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = db.Column(db.DateTime, nullable=True)

    creator = db.relationship('User', foreign_keys=[created_by])
    versions = db.relationship('DocumentVersion', backref='document', order_by='DocumentVersion.version_number.desc()')
    checkouts = db.relationship('CheckOut', backref='document')
    signoffs = db.relationship('SignOff', backref='document')
    notes = db.relationship('Note', backref='document', order_by='Note.created_at.desc()')

    @property
    def active_checkout(self):
        from models.workflow import CheckOut
        return CheckOut.query.filter_by(document_id=self.id, checked_in_at=None).first()

    @property
    def preparer_signoff(self):
        from models.workflow import SignOff
        return SignOff.query.filter_by(document_id=self.id, sign_off_type='preparer', cleared_at=None).first()

    @property
    def reviewer_signoff(self):
        from models.workflow import SignOff
        return SignOff.query.filter_by(document_id=self.id, sign_off_type='reviewer', cleared_at=None).first()

    @property
    def unresolved_notes_count(self):
        from models.workflow import Note
        return Note.query.filter_by(document_id=self.id, resolved=False).count()

    @property
    def latest_version(self):
        return self.versions[0] if self.versions else None

    def __repr__(self):
        return f'<Document {self.name}>'


class DocumentVersion(db.Model):
    __tablename__ = 'document_versions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    comment = db.Column(db.Text, default='')

    uploader = db.relationship('User', foreign_keys=[uploaded_by])
