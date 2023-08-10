from carpooling.models import CarpoolSolution, Organization, User, Event
from carpooling.utils import admin_required
from flask import render_template, Blueprint, session, request
from flask_login import current_user
import logging
from carpooling import db

admin_blueprint = Blueprint('admin', __name__, template_folder='templates')
logger = logging.getLogger(__name__)


@admin_blueprint.route('/valid-auth-keys')
@admin_required
def valid_auth_keys_page():
    """
    This page is only accessible if the admin has logged in.
    Page for admins to see all valid auth keys and when they were created.
    """
    pass
#     # querying the auth keys and ordering them
#     auth_keys = AuthKey.query.order_by(AuthKey.date_created).all()

#     # i love naming things
#     return_list = [item.key for item in auth_keys]
#     return_list_2 = [item.date_created for item in auth_keys]
#     return render_template('valid_auth_keys_template.html', return_list=zip(return_list, return_list_2), user=current_user)


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
    return render_template('manage_users_template.html', users=Organization.query.get(session['organization']).users, user=current_user )


@admin_blueprint.route('/view-checkins')
@admin_required
def view_checkins_page():
    """
    Function to view all the check ins.
    """
    recent_events = Event.query.order_by(
        Event.start_time.desc()).limit(3).all()
    other_events = Event.query.order_by(
        Event.start_time.desc()).offset(3).all()
    return render_template('view_checkins_template.html', recent_events=recent_events, other_events=other_events, user=current_user)


@admin_blueprint.route('/view-routes/<solution_id>')
@admin_required
def route_summary_page(solution_id):
    """
    Function to view the routes
    :param solution_id: the id of the solution to see
    """
    solution = CarpoolSolution.query.get(solution_id)
    generated_carpools = solution.generated_carpools
    event = solution.event
    all_solutions = sorted(event.generated_carpools, key=lambda f: f.id)
    # there is definitely a better way but im lazy
    for i, solution_ in enumerate(all_solutions):
        if solution_.id == solution.id:
            try:
                previous_solution_id = all_solutions[i-1].id
                next_solution_id = all_solutions[i+1].id
            except IndexError as e:
                logger.debug(e)
                if len(all_solutions) > i:
                    previous_solution_id = all_solutions[i-1].id
                    next_solution_id = all_solutions[0].id
                if i == 0:  # its a big lower
                    previous_solution_id = all_solutions[-1].id
                    next_solution_id = all_solutions[i+1].id
    
    logger.debug(f'{previous_solution_id} {next_solution_id}')
    return render_template('route_summary_template.html', event=event, user=current_user, carpool_solution=solution, generated_carpools=generated_carpools, next_solution_id=next_solution_id, previous_solution_id=previous_solution_id)

@admin_blueprint.route('/manage-organization')
@admin_required
def manage_organization_page():
    organization = Organization.query.get(int(session['organization']))
    return render_template('manage_organization_template.html', user=current_user, organization=organization)

@admin_blueprint.route('/edit-organization', methods=['GET', 'POST'])
@admin_required
def edit_organization_page():
    if request.method == 'GET':
        organization = Organization.query.get(int(session['organization']))
        return render_template('edit_organization_template.html', user=current_user, organization=organization)
    elif request.method == 'POST':
        organization = Organization.query.get(int(session['organization']))
        organization.name = request.form['organizationname']
        organization.description = request.form['organizationdescription']
        db.session.commit()
        return render_template('manage_organization_template.html', user=current_user, organization=organization)

