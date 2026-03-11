from flask import Blueprint, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models.binder import Binder, BinderAccess, Folder
from models.workflow import ActivityLog

folder_bp = Blueprint('folder', __name__, url_prefix='/folder')


def check_edit_access(binder):
    if current_user.is_admin():
        return True
    access = BinderAccess.query.filter_by(binder_id=binder.id, user_id=current_user.id).first()
    return access and access.access_level in ('owner', 'editor')


@folder_bp.route('/create', methods=['POST'])
@login_required
def create():
    binder_id = request.form.get('binder_id', type=int)
    parent_id = request.form.get('parent_id', type=int) or None
    name = request.form.get('name', '').strip()
    index_number = request.form.get('index_number', '').strip()

    binder = Binder.query.get_or_404(binder_id)
    if not check_edit_access(binder):
        flash('Access denied.', 'danger')
        return redirect(url_for('binder.view', binder_id=binder_id))

    max_order = db.session.query(db.func.max(Folder.sort_order))\
        .filter_by(binder_id=binder_id, parent_id=parent_id).scalar() or 0

    folder = Folder(binder_id=binder_id, parent_id=parent_id, name=name,
                    index_number=index_number, sort_order=max_order + 1)
    db.session.add(folder)

    log = ActivityLog(binder_id=binder_id, user_id=current_user.id,
                      action='created', target_type='folder', target_id=folder.id,
                      details=f'Created folder "{name}"')
    db.session.add(log)
    db.session.commit()

    flash(f'Folder "{name}" created.', 'success')
    return redirect(url_for('binder.view', binder_id=binder_id, folder_id=folder.id))


@folder_bp.route('/<int:folder_id>/rename', methods=['POST'])
@login_required
def rename(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    binder = Binder.query.get_or_404(folder.binder_id)
    if not check_edit_access(binder):
        return jsonify({'error': 'Access denied'}), 403

    name = request.form.get('name', '').strip()
    index_number = request.form.get('index_number', folder.index_number).strip()
    if name:
        folder.name = name
        folder.index_number = index_number
        db.session.commit()
        flash('Folder renamed.', 'success')

    return redirect(url_for('binder.view', binder_id=folder.binder_id, folder_id=folder.id))


@folder_bp.route('/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    binder = Binder.query.get_or_404(folder.binder_id)
    if not check_edit_access(binder):
        flash('Access denied.', 'danger')
        return redirect(url_for('binder.view', binder_id=folder.binder_id))

    binder_id = folder.binder_id
    # Soft-delete documents in folder
    from models.document import Document
    from datetime import datetime, timezone
    for doc in Document.query.filter_by(folder_id=folder.id, status='active').all():
        doc.status = 'deleted'
        doc.deleted_at = datetime.now(timezone.utc)

    db.session.delete(folder)
    db.session.commit()
    flash('Folder deleted.', 'success')
    return redirect(url_for('binder.view', binder_id=binder_id))


@folder_bp.route('/<int:folder_id>/move', methods=['POST'])
@login_required
def move(folder_id):
    """AJAX endpoint for drag-drop folder move."""
    folder = Folder.query.get_or_404(folder_id)
    binder = Binder.query.get_or_404(folder.binder_id)
    if not check_edit_access(binder):
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json() or {}
    new_parent_id = data.get('parent_id')
    new_sort_order = data.get('sort_order', 0)

    folder.parent_id = new_parent_id if new_parent_id else None
    folder.sort_order = new_sort_order
    db.session.commit()
    return jsonify({'ok': True})
