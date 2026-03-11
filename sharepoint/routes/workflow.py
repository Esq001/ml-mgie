from datetime import datetime, timezone
from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.document import Document
from models.workflow import SignOff, Note, ActivityLog

workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')


@workflow_bp.route('/signoff/<int:doc_id>', methods=['POST'])
@login_required
def signoff(doc_id):
    doc = Document.query.get_or_404(doc_id)
    sign_off_type = request.form.get('type')  # preparer or reviewer

    if sign_off_type not in ('preparer', 'reviewer'):
        flash('Invalid sign-off type.', 'danger')
        return redirect(url_for('document.detail', doc_id=doc_id))

    # Check if already signed off
    existing = SignOff.query.filter_by(
        document_id=doc.id, sign_off_type=sign_off_type, cleared_at=None
    ).first()
    if existing:
        flash(f'{sign_off_type.title()} sign-off already exists.', 'warning')
        return redirect(url_for('document.detail', doc_id=doc_id))

    so = SignOff(document_id=doc.id, sign_off_type=sign_off_type, signed_by=current_user.id)
    db.session.add(so)

    log = ActivityLog(binder_id=doc.binder_id, user_id=current_user.id,
                      action=f'{sign_off_type}_signoff', target_type='document', target_id=doc.id,
                      details=f'{sign_off_type.title()} sign-off on "{doc.name}"')
    db.session.add(log)
    db.session.commit()

    flash(f'{sign_off_type.title()} sign-off applied.', 'success')
    return redirect(url_for('document.detail', doc_id=doc_id))


@workflow_bp.route('/signoff/<int:signoff_id>/clear', methods=['POST'])
@login_required
def clear_signoff(signoff_id):
    so = SignOff.query.get_or_404(signoff_id)
    if so.signed_by != current_user.id and not current_user.is_admin():
        flash('Only the signer or admin can clear a sign-off.', 'danger')
        return redirect(url_for('document.detail', doc_id=so.document_id))

    so.cleared_at = datetime.now(timezone.utc)
    so.cleared_by = current_user.id
    db.session.commit()

    flash('Sign-off cleared.', 'success')
    return redirect(url_for('document.detail', doc_id=so.document_id))


@workflow_bp.route('/note/<int:doc_id>', methods=['POST'])
@login_required
def add_note(doc_id):
    doc = Document.query.get_or_404(doc_id)
    content = request.form.get('content', '').strip()
    if not content:
        flash('Note content is required.', 'danger')
        return redirect(url_for('document.detail', doc_id=doc_id))

    note = Note(document_id=doc.id, content=content, created_by=current_user.id)
    db.session.add(note)

    log = ActivityLog(binder_id=doc.binder_id, user_id=current_user.id,
                      action='added_note', target_type='document', target_id=doc.id,
                      details=f'Added note on "{doc.name}"')
    db.session.add(log)
    db.session.commit()

    flash('Note added.', 'success')
    return redirect(url_for('document.detail', doc_id=doc_id))


@workflow_bp.route('/note/<int:note_id>/resolve', methods=['POST'])
@login_required
def resolve_note(note_id):
    note = Note.query.get_or_404(note_id)
    note.resolved = True
    note.resolved_by = current_user.id
    note.resolved_at = datetime.now(timezone.utc)
    db.session.commit()

    flash('Note resolved.', 'success')
    return redirect(url_for('document.detail', doc_id=note.document_id))
