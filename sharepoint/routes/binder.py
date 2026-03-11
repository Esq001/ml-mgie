from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.binder import Binder, BinderAccess, Folder
from models.document import Document
from models.workflow import ActivityLog

binder_bp = Blueprint('binder', __name__, url_prefix='/binder')


def check_binder_access(binder, min_level='viewer'):
    if current_user.is_admin():
        return True
    access = BinderAccess.query.filter_by(binder_id=binder.id, user_id=current_user.id).first()
    if not access:
        return False
    levels = {'viewer': 0, 'editor': 1, 'owner': 2}
    return levels.get(access.access_level, 0) >= levels.get(min_level, 0)


@binder_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        client_name = request.form.get('client_name', '').strip()
        engagement_type = request.form.get('engagement_type', 'audit')
        description = request.form.get('description', '').strip()
        period_end = request.form.get('period_end_date', '')

        if not name or not client_name:
            flash('Name and client are required.', 'danger')
            return render_template('binder/create.html')

        binder = Binder(
            name=name, client_name=client_name, engagement_type=engagement_type,
            description=description, created_by=current_user.id,
            period_end_date=datetime.strptime(period_end, '%Y-%m-%d').date() if period_end else None
        )
        db.session.add(binder)
        db.session.flush()

        # Grant owner access to creator
        access = BinderAccess(binder_id=binder.id, user_id=current_user.id, access_level='owner')
        db.session.add(access)

        # Create default folder structure
        default_folders = [
            ('A', 'Planning', 1),
            ('B', 'Testing', 2),
            ('C', 'Completion', 3),
            ('D', 'Financial Statements', 4),
        ]
        for idx, fname, order in default_folders:
            folder = Folder(binder_id=binder.id, name=fname, index_number=idx, sort_order=order)
            db.session.add(folder)

        log = ActivityLog(binder_id=binder.id, user_id=current_user.id,
                          action='created', target_type='binder', target_id=binder.id,
                          details=f'Created binder "{name}"')
        db.session.add(log)
        db.session.commit()

        flash(f'Binder "{name}" created.', 'success')
        return redirect(url_for('binder.view', binder_id=binder.id))

    return render_template('binder/create.html')


@binder_bp.route('/<int:binder_id>')
@login_required
def view(binder_id):
    binder = Binder.query.get_or_404(binder_id)
    if not check_binder_access(binder):
        flash('Access denied.', 'danger')
        return redirect(url_for('fileroom.index'))

    folder_id = request.args.get('folder_id', type=int)
    show_deleted = request.args.get('recycle', '') == '1'

    # Build folder tree (root folders)
    root_folders = Folder.query.filter_by(binder_id=binder.id, parent_id=None)\
        .order_by(Folder.sort_order).all()

    # Get documents for selected folder or all
    if show_deleted:
        documents = Document.query.filter_by(binder_id=binder.id, status='deleted')\
            .order_by(Document.name).all()
        selected_folder = None
    elif folder_id:
        documents = Document.query.filter_by(folder_id=folder_id, status='active')\
            .order_by(Document.name).all()
        selected_folder = Folder.query.get(folder_id)
    else:
        documents = Document.query.filter_by(binder_id=binder.id, status='active')\
            .order_by(Document.name).all()
        selected_folder = None

    # Access info
    access = BinderAccess.query.filter_by(binder_id=binder.id, user_id=current_user.id).first()
    user_access_level = 'owner' if current_user.is_admin() else (access.access_level if access else 'viewer')

    # Activity log (recent)
    activities = ActivityLog.query.filter_by(binder_id=binder.id)\
        .order_by(ActivityLog.created_at.desc()).limit(20).all()

    return render_template('binder/view.html', binder=binder, root_folders=root_folders,
                           documents=documents, selected_folder=selected_folder,
                           user_access_level=user_access_level, show_deleted=show_deleted,
                           activities=activities)


@binder_bp.route('/<int:binder_id>/edit', methods=['POST'])
@login_required
def edit(binder_id):
    binder = Binder.query.get_or_404(binder_id)
    if not check_binder_access(binder, 'owner'):
        flash('Access denied.', 'danger')
        return redirect(url_for('binder.view', binder_id=binder_id))

    binder.name = request.form.get('name', binder.name).strip()
    binder.client_name = request.form.get('client_name', binder.client_name).strip()
    binder.engagement_type = request.form.get('engagement_type', binder.engagement_type)
    binder.description = request.form.get('description', binder.description).strip()
    period_end = request.form.get('period_end_date', '')
    if period_end:
        binder.period_end_date = datetime.strptime(period_end, '%Y-%m-%d').date()

    db.session.commit()
    flash('Binder updated.', 'success')
    return redirect(url_for('binder.view', binder_id=binder_id))


@binder_bp.route('/<int:binder_id>/archive', methods=['POST'])
@login_required
def archive(binder_id):
    binder = Binder.query.get_or_404(binder_id)
    if not check_binder_access(binder, 'owner'):
        flash('Access denied.', 'danger')
        return redirect(url_for('binder.view', binder_id=binder_id))

    binder.status = 'archived' if binder.status == 'active' else 'active'
    db.session.commit()
    flash(f'Binder {"archived" if binder.status == "archived" else "restored"}.', 'success')
    return redirect(url_for('fileroom.index'))


@binder_bp.route('/<int:binder_id>/access', methods=['POST'])
@login_required
def manage_access(binder_id):
    binder = Binder.query.get_or_404(binder_id)
    if not check_binder_access(binder, 'owner'):
        flash('Access denied.', 'danger')
        return redirect(url_for('binder.view', binder_id=binder_id))

    action = request.form.get('action')
    user_id = request.form.get('user_id', type=int)
    access_level = request.form.get('access_level', 'viewer')

    if action == 'add' and user_id:
        existing = BinderAccess.query.filter_by(binder_id=binder_id, user_id=user_id).first()
        if existing:
            existing.access_level = access_level
        else:
            db.session.add(BinderAccess(binder_id=binder_id, user_id=user_id, access_level=access_level))
        db.session.commit()
        flash('Access updated.', 'success')
    elif action == 'remove' and user_id:
        BinderAccess.query.filter_by(binder_id=binder_id, user_id=user_id).delete()
        db.session.commit()
        flash('Access removed.', 'success')

    return redirect(url_for('binder.view', binder_id=binder_id))
