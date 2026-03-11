import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from models import db
from models.binder import Binder, BinderAccess, Folder
from models.document import Document, DocumentVersion
from models.workflow import CheckOut, ActivityLog

document_bp = Blueprint('document', __name__, url_prefix='/document')


def check_edit_access(binder):
    if current_user.is_admin():
        return True
    access = BinderAccess.query.filter_by(binder_id=binder.id, user_id=current_user.id).first()
    return access and access.access_level in ('owner', 'editor')


@document_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    binder_id = request.form.get('binder_id', type=int)
    folder_id = request.form.get('folder_id', type=int)
    binder = Binder.query.get_or_404(binder_id)
    if not check_edit_access(binder):
        flash('Access denied.', 'danger')
        return redirect(url_for('binder.view', binder_id=binder_id))

    file = request.files.get('file')
    if not file or file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('binder.view', binder_id=binder_id, folder_id=folder_id))

    filename = file.filename
    file_ext = os.path.splitext(filename)[1].lower()
    stored_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
    file.save(file_path)
    file_size = os.path.getsize(file_path)

    doc = Document(
        folder_id=folder_id, binder_id=binder_id, name=filename,
        file_type=file_ext.lstrip('.'), current_version=1,
        created_by=current_user.id
    )
    db.session.add(doc)
    db.session.flush()

    version = DocumentVersion(
        document_id=doc.id, version_number=1, file_path=stored_name,
        file_size=file_size, uploaded_by=current_user.id, comment='Initial upload'
    )
    db.session.add(version)

    log = ActivityLog(binder_id=binder_id, user_id=current_user.id,
                      action='uploaded', target_type='document', target_id=doc.id,
                      details=f'Uploaded "{filename}"')
    db.session.add(log)
    db.session.commit()

    flash(f'"{filename}" uploaded.', 'success')
    return redirect(url_for('binder.view', binder_id=binder_id, folder_id=folder_id))


@document_bp.route('/<int:doc_id>')
@login_required
def detail(doc_id):
    doc = Document.query.get_or_404(doc_id)
    binder = Binder.query.get_or_404(doc.binder_id)

    access = BinderAccess.query.filter_by(binder_id=binder.id, user_id=current_user.id).first()
    if not current_user.is_admin() and not access:
        flash('Access denied.', 'danger')
        return redirect(url_for('fileroom.index'))

    user_access_level = 'owner' if current_user.is_admin() else (access.access_level if access else 'viewer')

    return render_template('document/detail.html', doc=doc, binder=binder,
                           user_access_level=user_access_level)


@document_bp.route('/<int:doc_id>/download')
@document_bp.route('/<int:doc_id>/download/<int:version_id>')
@login_required
def download(doc_id, version_id=None):
    doc = Document.query.get_or_404(doc_id)
    if version_id:
        version = DocumentVersion.query.get_or_404(version_id)
    else:
        version = doc.latest_version

    if not version:
        flash('No file version found.', 'danger')
        return redirect(url_for('document.detail', doc_id=doc_id))

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], version.file_path)
    if not os.path.exists(file_path):
        flash('File not found on disk.', 'danger')
        return redirect(url_for('document.detail', doc_id=doc_id))

    return send_file(file_path, download_name=doc.name, as_attachment=True)


@document_bp.route('/<int:doc_id>/checkout', methods=['POST'])
@login_required
def checkout(doc_id):
    doc = Document.query.get_or_404(doc_id)
    binder = Binder.query.get_or_404(doc.binder_id)
    if not check_edit_access(binder):
        flash('Access denied.', 'danger')
        return redirect(url_for('document.detail', doc_id=doc_id))

    if doc.active_checkout:
        flash(f'Already checked out by {doc.active_checkout.user.full_name}.', 'warning')
        return redirect(url_for('document.detail', doc_id=doc_id))

    co = CheckOut(document_id=doc.id, checked_out_by=current_user.id)
    db.session.add(co)

    log = ActivityLog(binder_id=doc.binder_id, user_id=current_user.id,
                      action='checked_out', target_type='document', target_id=doc.id,
                      details=f'Checked out "{doc.name}"')
    db.session.add(log)
    db.session.commit()

    flash(f'"{doc.name}" checked out.', 'success')
    return redirect(url_for('document.detail', doc_id=doc_id))


@document_bp.route('/<int:doc_id>/checkin', methods=['POST'])
@login_required
def checkin(doc_id):
    doc = Document.query.get_or_404(doc_id)
    co = doc.active_checkout
    if not co:
        flash('Document is not checked out.', 'warning')
        return redirect(url_for('document.detail', doc_id=doc_id))

    if co.checked_out_by != current_user.id and not current_user.is_admin():
        flash('Only the person who checked out or an admin can check in.', 'danger')
        return redirect(url_for('document.detail', doc_id=doc_id))

    co.checked_in_at = datetime.now(timezone.utc)

    # Handle optional new version upload
    file = request.files.get('file')
    comment = request.form.get('comment', '').strip()
    if file and file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        stored_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        doc.current_version += 1
        doc.name = file.filename
        doc.file_type = file_ext.lstrip('.')

        version = DocumentVersion(
            document_id=doc.id, version_number=doc.current_version,
            file_path=stored_name, file_size=file_size,
            uploaded_by=current_user.id, comment=comment or 'Check-in upload'
        )
        db.session.add(version)

    log = ActivityLog(binder_id=doc.binder_id, user_id=current_user.id,
                      action='checked_in', target_type='document', target_id=doc.id,
                      details=f'Checked in "{doc.name}"')
    db.session.add(log)
    db.session.commit()

    flash(f'"{doc.name}" checked in.', 'success')
    return redirect(url_for('document.detail', doc_id=doc_id))


@document_bp.route('/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete(doc_id):
    doc = Document.query.get_or_404(doc_id)
    binder = Binder.query.get_or_404(doc.binder_id)
    if not check_edit_access(binder):
        flash('Access denied.', 'danger')
        return redirect(url_for('document.detail', doc_id=doc_id))

    doc.status = 'deleted'
    doc.deleted_at = datetime.now(timezone.utc)

    log = ActivityLog(binder_id=doc.binder_id, user_id=current_user.id,
                      action='deleted', target_type='document', target_id=doc.id,
                      details=f'Deleted "{doc.name}"')
    db.session.add(log)
    db.session.commit()

    flash(f'"{doc.name}" moved to recycle bin.', 'success')
    return redirect(url_for('binder.view', binder_id=doc.binder_id, folder_id=doc.folder_id))


@document_bp.route('/<int:doc_id>/restore', methods=['POST'])
@login_required
def restore(doc_id):
    doc = Document.query.get_or_404(doc_id)
    binder = Binder.query.get_or_404(doc.binder_id)
    if not check_edit_access(binder):
        flash('Access denied.', 'danger')
        return redirect(url_for('binder.view', binder_id=doc.binder_id, recycle='1'))

    doc.status = 'active'
    doc.deleted_at = None
    db.session.commit()

    flash(f'"{doc.name}" restored.', 'success')
    return redirect(url_for('binder.view', binder_id=doc.binder_id, recycle='1'))


@document_bp.route('/<int:doc_id>/move', methods=['POST'])
@login_required
def move(doc_id):
    doc = Document.query.get_or_404(doc_id)
    binder = Binder.query.get_or_404(doc.binder_id)
    if not check_edit_access(binder):
        flash('Access denied.', 'danger')
        return redirect(url_for('document.detail', doc_id=doc_id))

    new_folder_id = request.form.get('folder_id', type=int)
    if new_folder_id:
        folder = Folder.query.get(new_folder_id)
        if folder and folder.binder_id == doc.binder_id:
            doc.folder_id = new_folder_id
            db.session.commit()
            flash('Document moved.', 'success')

    return redirect(url_for('document.detail', doc_id=doc_id))
