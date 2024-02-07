
import math
import os
import uuid

from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.view import view_config, forbidden_view_config
from ..models.environment_access_requester import Environment_Access_Requester
from ..utilities.cognito import Cognito
from ..utilities.dynamodb import DynamoDB

@forbidden_view_config()
def forbidden_view(request):
    redirect_url = HTTPFound(location=request.route_url('login'))
    return redirect_url

######################################################################################
# LOGIN VIEWS:
######################################################################################

@view_config(route_name='login', renderer='self_service_portal:templates/login/login.jinja2')
def login(request):
    messages = request.session.pop_flash()
    if (request.authenticated_userid):
        redirect_url = HTTPFound(location=request.route_url('home'))
        return redirect_url
    if request.method == "POST":
        login_post_action(request)
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Welcome',
        'message': messages
    }

@view_config(route_name='change-password-force', renderer='self_service_portal:templates/login/passwords/force_password_change.jinja2')
def change_password_force(request):
    messages = request.session.pop_flash()
    if request.method == "POST":
        change_password_force_post_action(request)
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Change Your Password',
        'message': messages
     }

@view_config(route_name='change-password-reset-request', renderer='self_service_portal:templates/login/passwords/password_reset_request.jinja2')
def change_password_reset_request(request):
    if request.method == "POST":
        change_password_reset_request_post_action(request)
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Password Reset Request',
     }

@view_config(route_name='change-password', renderer='self_service_portal:templates/login/passwords/change_password.jinja2')
def change_password_request(request):
    messages = request.session.pop_flash()
    if request.method == "POST":
        change_password_request_post_action(request)
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Change Your Password',
        'message': messages
     }

@view_config(route_name='mfa-setup', renderer='self_service_portal:templates/login/mfa/mfa_setup.jinja2')
def multi_factor_auth_setup(request):
    qr_image = request.session.get('qr_code_path', 'Default')
    if request.method == "POST":
        multi_factor_auth_setup_post_action(request)
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Multi-Factor Authentication Setup',
        'qr_image': qr_image
    }

@view_config(route_name='mfa-request', renderer='self_service_portal:templates/login/mfa/mfa_request.jinja2')
def multi_factor_auth_verification(request):
    if request.method == "POST":
        multi_factor_auth_verification_post_action(request)
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Multi-Factor Authentication Request',
    }

@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    url = request.route_url('login')
    return HTTPFound(location=url, headers=headers)

######################################################################################
# LOGIN FUNCTIONS:
######################################################################################

def login_post_action(request):
    form_data = request.params
    email = form_data.get('emailAddress')
    password = form_data.get('password')
    request.session['email_address'] = email
    cognito_instance = Cognito(request)
    password_check = cognito_instance.check_force_password_change_status()
    if password_check is True:
        redirect_url = request.route_url('change-password-force')
        raise HTTPFound(redirect_url)
    if password_check is False:
        response = cognito_instance.handle_initiate_authentication(password)
        cognito_instance.handle_auth_response(response)

def change_password_force_post_action(request):
    form_data = request.params
    email = form_data.get('emailAddress')
    new_password = form_data.get('newPassword')
    request.session['email_address'] = email
    cognito_instance = Cognito(request)
    cognito_instance.handle_force_password_change(new_password)
    request.session.flash('Password Changed')
    redirect_url = request.route_url('login')
    raise HTTPFound(redirect_url)

def change_password_reset_request_post_action(request):
    form_data = request.params
    email = form_data.get('emailAddress')
    request.session['email_address'] = email
    cognito_instance = Cognito(request)
    cognito_instance.handle_password_reset_request()
    redirect_url = request.route_url('change-password')
    raise HTTPFound(redirect_url)

def change_password_request_post_action(request):
    form_data = request.params
    email = form_data.get('emailAddress')
    new_password = form_data.get('newPassword')
    verification_code = form_data.get('verificationCode')
    request.session['email_address'] = email
    cognito_instance = Cognito(request)
    cognito_instance.handle_password_reset(verification_code, new_password)
    request.session.flash('Password Changed')
    redirect_url = request.route_url('login')
    raise HTTPFound(redirect_url)

def multi_factor_auth_setup_post_action(request):
    form_data = request.params
    verification_code = form_data.get('authVerificationCode')
    cognito_instance = Cognito(request)
    cognito_instance.handle_verify_software_token(request, verification_code)
    cognito_instance.handle_mfa_user_preferences()
    os.remove(request.session['qr_code_path'])
    request.session.flash('MFA Setup')
    redirect_url = request.route_url('login')
    raise HTTPFound(redirect_url)

def multi_factor_auth_verification_post_action(request):
    form_data = request.params
    verification_code = form_data.get('authVerificationCode')
    cognito_instance = Cognito(request)
    mfa_verification = cognito_instance.handle_respond_to_auth_challenge(request, verification_code)
    if mfa_verification["ChallengeParameters"] == {}:
        headers = remember(request, request.session['email_address'])
        redirect_url = request.route_url('home')
        raise HTTPFound(redirect_url, headers=headers)

######################################################################################
# HOME / DASHBOARD VIEWS:
######################################################################################

@view_config(route_name='home', renderer='self_service_portal:templates/home.jinja2', permission='protected')
def home_view(request):
    return { 'subtitle': 'Self Service Portal', 'title': 'Home' }

######################################################################################
# ENVIRONMENT ACCESS VIEWS:
######################################################################################

@view_config(route_name='env-dashboard', renderer='self_service_portal:templates/env_access/env_dashboard.jinja2', permission='protected')
def env_dashboard_view(request):
    messages = request.session.pop_flash()
    dynamodb_table = dynamodb_table_connection(request)
    form_data = request.params
    selected_status = form_data.get('status')
    selected_environment = form_data.get('environment')
    response = query_results(dynamodb_table, selected_status, selected_environment)
    items = response.get('Items', [])
    sorted_items = sorted(items, key=lambda x: ( x.get('access-status', ''), datetime.strptime(x.get('access-request-date'), '%d/%m/%Y %H:%M') ), reverse=True)
    status_counts = get_status_counts(sorted_items)
    page = int(request.params.get('page', 1))
    items_per_page = 10
    total_pages = math.ceil(len(sorted_items) / items_per_page)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_items = sorted_items[start_index:end_index]

    return {
        'subtitle': 'Environment Access',
        'title': 'Dashboard',
        'message': messages,
        'result': paginated_items,
        'selected_status': selected_status,
        'selected_environment': selected_environment,
        'status_counts': status_counts,
        'page': page,
        'total_pages': total_pages,
    }

@view_config(route_name='env-new-request', renderer='self_service_portal:templates/env_access/env_new_request.jinja2', permission='protected')
def env_new_request_view(request):
    if request.method == "POST":
        form_data = request.params
        item = {
            'Request-ID': str(uuid.uuid4()),
            'access-first-name': form_data.get('firstName'),
            'access-last-name': form_data.get('lastName'),
            'access-team': form_data.get('teamName'),
            'access-environment': form_data.get('environmentRequired'),
            'access-email-address': form_data.get('emailAddress'),
            'access-status': 'Pending',
            'access-request-date': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'access-comments': form_data.get('requestComments'),
        }
        region_name = request.registry.settings.get('dynamodb.region_name')
        table_name = request.registry.settings.get('dynamodb.table_name')
        dynamodb_service = DynamoDB(region_name, table_name)
        dynamodb_table = dynamodb_service.get_table()
        dynamodb_table.add_record(item)
        request.session.flash('Record Submitted')
        redirect_url = request.route_url('env-dashboard')
        raise HTTPFound(redirect_url)

    return {
        'subtitle': 'Environment Access',
        'title': 'New Request'
    }

@view_config(route_name='env-request', renderer='self_service_portal:templates/env_access/env_existing_request.jinja2', permission='protected')
def env_request_view(request):
    messages = request.session.pop_flash()
    request_id = request.matchdict['id']
    dynamodb_table = dynamodb_table_connection(request)
    response = dynamodb_table.query(
        KeyConditionExpression=Key('Request-ID').eq(request_id)
    )
    for item in response['Items']:
        requester_info = Environment_Access_Requester(item.get('access-first-name'), item.get('access-last-name'), item.get('access-email-address'), item.get('access-team'), item.get('access-environment'), item.get('access-status'), item.get('access-comments'), item.get('access-request-date'), item.get('admin-full-name'), item.get('admin-response-date'), item.get('admin-comments') )
    if request.method == "POST":
        form_data = request.params
        update_expression = "SET #access_status = :access_form_status, #admin_comments = :admin_form_comments, #admin_full_name = :admin_form_full_name, #admin_response_date = :admin_form_response_date, #notification_alert = :notification_alert"
        expression_attribute_names = {
            '#access_status': 'access-status',
            '#admin_comments': 'admin-comments',
            '#admin_full_name': 'admin-full-name',
            '#admin_response_date': 'admin-response-date',
            '#notification_alert': 'notification-alert'
        }
        expression_attribute_values = {
            ':access_form_status': form_data.get('adminStatus'),
            ':admin_form_comments': form_data.get('adminComments'),
            ':admin_form_full_name': 'Ryan Jackson',
            ':admin_form_response_date': datetime.now().strftime("%d/%m/%Y %H:%M"),
            ':notification_alert': 'false',
        }
        dynamodb_table.update_record(request_id, update_expression, expression_attribute_names, expression_attribute_values)
        request.session.flash('Record Updated')

    return {
        'subtitle': 'Environment Access',
        'title': requester_info.first_name + ' ' + requester_info.last_name,
        'requester_info': requester_info,
        'message': messages
    }

@view_config(route_name='env-admin-control-panel', renderer='self_service_portal:templates/env_access/admin/request_control_panel.jinja2', permission='admin')
def env_admin_control_panel_view(request):
    messages = request.session.pop_flash()
    request_id = request.matchdict['id']
    dynamodb_table = dynamodb_table_connection(request)
    response = dynamodb_table.query(
        KeyConditionExpression=Key('Request-ID').eq(request_id)
    )
    for item in response['Items']:
        requester_info = Environment_Access_Requester(item.get('access-first-name'), item.get('access-last-name'), item.get('access-email-address'), item.get('access-team'), item.get('access-environment'), item.get('access-status'), item.get('access-comments'), item.get('access-request-date'), item.get('admin-full-name'), item.get('admin-response-date'), item.get('admin-comments') )
    if request.method == "POST":
        form_data = request.params
        if form_data.get('AdminControlPanel') == "Update":
            update_expression = "SET #access_email_address = :access_email_address, #access_environment = :access_environment, #access_first_name = :access_first_name, #access_last_name = :access_last_name, #access_request_date = :access_request_date, #access_status = :access_status, #access_team = :access_team, #admin_full_name = :admin_full_name, #admin_comments = :admin_comments, #admin_response_date = :admin_response_date, #notification_alert = :notification_alert"
            expression_attribute_names = {
                '#access_email_address': 'access-email-address',
                '#access_environment': 'access-environment',
                '#access_first_name': 'access-first-name',
                '#access_last_name': 'access-last-name',
                '#access_request_date': 'access-request-date',
                '#access_status': 'access-status',
                '#access_team': 'access-team',
                '#admin_full_name': 'admin-full-name',
                '#admin_comments': 'admin-comments',
                '#admin_response_date': 'admin-response-date',
                '#notification_alert': 'notification-alert',
            }
            expression_attribute_values = {
                ':access_email_address': form_data.get('emailAddress'),
                ':access_environment': form_data.get('environmentRequired'),
                ':access_first_name': form_data.get('firstName'),
                ':access_last_name': form_data.get('lastName'),
                ':access_request_date': form_data.get('requestDate'),
                ':access_status': form_data.get('requestStatus'),
                ':access_team': form_data.get('teamName'),
                ':admin_full_name': 'Ryan Jackson',
                ':admin_comments': form_data.get('adminComments'),
                ':admin_response_date': datetime.now().strftime("%d/%m/%Y %H:%M"),
                ':notification_alert': 'false',
            }
            dynamodb_table.update_record(request_id, update_expression, expression_attribute_names, expression_attribute_values)
            request.session.flash('Record Updated')
        if form_data.get('AdminControlPanel') == "Delete":
            dynamodb_table.delete_record(request_id)
            request.session.flash('Record Deleted')
            raise HTTPFound(request.route_url('env-dashboard'))

    return {
        'subtitle': 'Environment Access - Admin Control Panel',
        'title': requester_info.first_name + ' ' + requester_info.last_name + ' - Admin Control Panel',
        'requester_info': requester_info,
        'current_date_time': datetime.now().strftime("%d/%m/%Y %H:%M"),
        'message': messages
    }

@view_config(route_name='env-export-data', renderer='self_service_portal:templates/env_access/admin/export_data.jinja2', permission='admin')
def env_export_data_view(request):
    dynamodb_table = dynamodb_table_connection(request)
    form_data = request.params
    selected_status = form_data.get('status')
    selected_environment = form_data.get('environment')
    response = query_results(dynamodb_table, selected_status, selected_environment)
    items = response.get('Items', [])
    sorted_items = sorted(items, key=lambda x: ( x.get('access-status', ''), datetime.strptime(x.get('access-request-date'), '%d/%m/%Y %H:%M') ), reverse=True)
    status_counts = get_status_counts(sorted_items)
    if request.method == "POST":
        csv_content = env_export_data_view_post(sorted_items)
        csv_response = Response(content_type='text/csv')
        csv_response.content_disposition = 'attachment;filename=exported_data.csv'
        csv_response.text = csv_content
        return csv_response

    return {
        'subtitle': 'Environment Access',
        'title': 'Export Data',
        'result': sorted_items,
        'selected_status': selected_status,
        'selected_environment': selected_environment,
        'status_counts': status_counts
    }

######################################################################################
# ENVIRONMENT ACCESS FUNCTIONS:
######################################################################################

def dynamodb_table_connection(request):
    region_name = request.registry.settings.get('dynamodb.region_name')
    table_name = request.registry.settings.get('dynamodb.table_name')
    dynamodb_service = DynamoDB(region_name, table_name)
    dynamodb_table = dynamodb_service.get_table()
    return dynamodb_table

def query_results(dynamodb_table, selected_status, selected_environment):
    status_condition = None
    environment_condition = None
    scan_parameters = {}
    expression_attribute_names = {}
    expression_attribute_values = {}
    if selected_status:
        status_condition = '#access_status = :status'
        expression_attribute_names['#access_status'] = 'access-status'
        expression_attribute_values[':status'] = selected_status
    if selected_environment:
        environment_condition = '#access_environment = :environment'
        if status_condition :
            status_condition = status_condition + ' AND ' + environment_condition
        else:
            status_condition = environment_condition
        expression_attribute_names['#access_environment'] = 'access-environment'
        expression_attribute_values[':environment'] = selected_environment
    if selected_status or selected_environment:
        scan_parameters['FilterExpression'] = status_condition
        scan_parameters['ExpressionAttributeNames'] = expression_attribute_names
        scan_parameters['ExpressionAttributeValues'] = expression_attribute_values
    try:
        response = dynamodb_table.scan(**scan_parameters)
    except Exception as e:
        raise HTTPNotFound from e
    return response

def get_status_counts(sorted_items):
    status_type = ["Pending", "Approved", "Denied"]
    status_counts = {status: 0 for status in ['total_requests'] + [f'{status.lower()}_requests' for status in status_type]}
    for item in sorted_items:
        status_counts['total_requests'] += 1
        status = item.get('access-status')
        if status in status_type:
            status_counts[f'{status.lower()}_requests'] += 1
        else:
            status_counts['all_requests'] += 1
    return status_counts

def env_export_data_view_post(data):
    csv_content = ''
    if data:
        csv_content += ','.join(data[0].keys()) + '\n'
        for row in data:
            csv_content += ','.join(map(str, row.values())) + '\n'
    return csv_content

######################################################################################
# ENVIRONMENT URL VIEWS:
######################################################################################

@view_config(route_name='env-generate', renderer='self_service_portal:templates/env_generate/env_generate_url.jinja2', permission='protected')
def env_generate_view(request):
    approved_environments = get_approved_environments(request)
    return {
        'subtitle': 'Environment URL\'s',
        'title': 'Generate Environment URL',
        'environments': approved_environments
    }

@view_config(route_name='env-update', renderer='self_service_portal:templates/env_generate/env_update_url.jinja2', permission='protected')
def env_update_view(request):
    return {
        'subtitle': 'Environment URL\'s',
        'title': 'Update URL\'s'
    }

######################################################################################
# ENVIRONMENT URL FUNCTIONS:
######################################################################################

def get_approved_environments(request):
    dynamodb_table = dynamodb_table_connection(request)
    try:
        response = dynamodb_table.scan(FilterExpression=Attr('access-status').eq("Approved") & Key('access-email-address').eq(request.authenticated_userid))
    except Exception as e:
        raise HTTPNotFound from e
    items = response.get('Items', [])
    sorted_items = sorted(items, key=lambda x: ( x.get('access-environment') ))
    return sorted_items
