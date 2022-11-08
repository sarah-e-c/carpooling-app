from carpooling.models import  AuthKey, User, Event
from carpooling.utils import  admin_required
from flask import render_template
from flask_login import current_user
from flask import Blueprint

admin_blueprint = Blueprint('admin', __name__, template_folder='templates')


@admin_blueprint.route('/valid-auth-keys')
@admin_required
def valid_auth_keys_page():
    """
    This page is only accessible if the admin has logged in.
    Page for admins to see all valid auth keys and when they were created.
    """
    # querying the auth keys and ordering them
    auth_keys = AuthKey.query.order_by(AuthKey.date_created).all()

    # i love naming things
    return_list = [item.key for item in auth_keys]
    return_list_2 = [item.date_created for item in auth_keys]
    return render_template('valid_auth_keys_template.html', return_list=zip(return_list, return_list_2), user=current_user)

@admin_blueprint.route('/admin')
@admin_required
def admin_home_page():
    """
    Page that allows for creation of events, creation of regions, and viewing of the valid authorization keys
    """
    return render_template('admin_home_template.html', user=current_user)



@admin_blueprint.route('/manage-users')
@admin_required
def manage_users_page():
    """
    Admin page that allows for the management of users
    """
    return render_template('manage_users_template.html', users=User.query.order_by(User.is_admin.desc()).all(), user=current_user)


@admin_blueprint.route('/view-checkins')
@admin_required
def view_checkins():
    """
    Function to view all the check ins.
    """
    recent_events = Event.query.order_by(Event.event_start_time.desc()).limit(3).all()
    other_events = Event.query.order_by(Event.event_start_time.desc()).offset(3).all()
    return render_template('view_checkins_template.html', recent_events=recent_events, other_events=other_events, user=current_user)
