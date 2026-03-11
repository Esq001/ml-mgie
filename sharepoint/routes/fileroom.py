from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models.binder import Binder, BinderAccess

fileroom_bp = Blueprint('fileroom', __name__)


@fileroom_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'active')
    type_filter = request.args.get('type', '')

    if current_user.is_admin():
        query = Binder.query
    else:
        accessible_ids = [a.binder_id for a in BinderAccess.query.filter_by(user_id=current_user.id).all()]
        query = Binder.query.filter(Binder.id.in_(accessible_ids))

    if status_filter:
        query = query.filter_by(status=status_filter)
    if type_filter:
        query = query.filter_by(engagement_type=type_filter)

    binders = query.order_by(Binder.updated_at.desc()).all()
    return render_template('fileroom/index.html', binders=binders,
                           status_filter=status_filter, type_filter=type_filter)
