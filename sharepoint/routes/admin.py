from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.user import User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin():
        flash('Admin access required.', 'danger')
        return redirect(url_for('fileroom.index'))


@admin_bp.route('/users')
def users():
    all_users = User.query.order_by(User.full_name).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ('admin', 'manager', 'staff'):
        user.role = new_role
        db.session.commit()
        flash(f'{user.full_name} is now {new_role}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate yourself.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'{user.full_name} {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.users'))
