
import math
import os
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.view import view_config, forbidden_view_config
from ..utilities.cognito import Cognito
from ..utilities.dynamodb import DynamoDB

@forbidden_view_config()
def forbidden_view(request):
    # Use HTTPFound to create a redirect response:
    redirect_url = request.route_url('login')
    response = HTTPFound(location=redirect_url)
    return response

@view_config(route_name='login', renderer='self_service_portal:templates/login/login.jinja2')
def login(request):
    # Redirect user back to home if they have an active session:
    if (request.authenticated_userid):
        redirect_url = request.route_url('home')
        response = HTTPFound(location=redirect_url)
        return response
    # Pop the flash message up on return on HTTP POST:
    messages = request.session.pop_flash()
    # Login into the self service user portal:
    if request.method == "POST":
        login_post_action(request)
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Welcome',
        'message': messages
    }

@view_config(route_name='change-password-force', renderer='self_service_portal:templates/login/passwords/force_password_change.jinja2')
def change_password_force(request):
    # Pop the flash message up on return on HTTP POST:
    messages = request.session.pop_flash()
    # Complete a force password change for the user:
    if request.method == "POST":
        change_password_force_post_action(request)
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Change Your Password',
        'message': messages
     }

@view_config(route_name='change-password-reset-request', renderer='self_service_portal:templates/login/passwords/password_reset_request.jinja2')
def change_password_reset_request(request):
    # User requests to reset their password:
    if request.method == "POST":
        change_password_reset_request_post_action(request)
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Password Reset Request',
     }

@view_config(route_name='change-password', renderer='self_service_portal:templates/login/passwords/change_password.jinja2')
def change_password_request(request):
    # Pop the flash message up on return on HTTP POST:
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
    # Ability to setup TOTP, display QR code and allow user to input verification code:
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
    # Clear the user's session or any authentication-related information:
    headers = forget(request)
    url = request.route_url('login')
    return HTTPFound(location=url, headers=headers)

@view_config(route_name='home', renderer='self_service_portal:templates/home.jinja2', permission='protected')
def home_view(request):
    return { 'subtitle': 'Self Service Portal', 'title': 'Home' }

######################################################################################
######################################################################################
######################################################################################
######################################################################################

@view_config(route_name='env-dashboard', renderer='self_service_portal:templates/env_access/env_dashboard.jinja2', permission='protected')
def env_dashboard_view(request):
    # Pop the flash message up on return on HTTP POST:
    messages = request.session.pop_flash()
    # Create the connection to the DynamoDB table:
    region_name = request.registry.settings.get('dynamodb.region_name')
    table_name = request.registry.settings.get('dynamodb.table_name')
    dynamodb_service = DynamoDB(region_name, table_name)
    dynamodb_table = dynamodb_service.get_table()
    # Get form data from the dashboard:
    form_data = request.params
    selected_status = form_data.get('status')
    selected_environment = form_data.get('environment')
    # Define condition expressions and attribute values based on the selected filters:
    scan_parameters = {}
    expression_attribute_names = {}
    expression_attribute_values = {}
    status_condition = None
    environment_condition = None
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
    # Perform a query to fetch records from DynamoDB with the conditions:
    if selected_status or selected_environment:
        scan_parameters['FilterExpression'] = status_condition
        scan_parameters['ExpressionAttributeNames'] = expression_attribute_names
        scan_parameters['ExpressionAttributeValues'] = expression_attribute_values
    try:
        response = dynamodb_table.scan(**scan_parameters)
    except Exception as e:
        raise HTTPNotFound from e
    # Extract the items and last evaluated key from the response:
    items = response.get('Items', [])
    # Arrange the records by status and request date:
    sorted_items = sorted(items, key=lambda x: ( x.get('access-status', ''), datetime.strptime(x.get('access-request-date'), '%d/%m/%Y %H:%M') ), reverse=True)
    # Calculate total pages:
    items_per_page = 10
    total_items = len(sorted_items)
    total_pages = math.ceil(total_items / items_per_page)
    # Calculate start and end indices for slicing based on the current page:
    page = int(request.params.get('page', 1))
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    # Slice the sorted items based on pagination:
    paginated_items = sorted_items[start_index:end_index]
    # Get the number of requests for each status:
    status_type = ["Pending", "Approved", "Denied"]
    status_counts = {status: 0 for status in ['total_requests'] + [f'{status.lower()}_requests' for status in status_type]}
    for item in sorted_items:
        status_counts['total_requests'] += 1
        status = item.get('access-status')
        if status in status_type:
            status_counts[f'{status.lower()}_requests'] += 1
        else:
            # Increment all_requests even if status is not found:
            status_counts['all_requests'] += 1
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
        # Output the form data to an JSON object ready for adding to the DynamoDB table:
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
        # Create the connection to the DynamoDB table and add the new request record:
        region_name = request.registry.settings.get('dynamodb.region_name')
        table_name = request.registry.settings.get('dynamodb.table_name')
        dynamodb_service = DynamoDB(region_name, table_name)
        dynamodb_table = dynamodb_service.get_table()
        dynamodb_table.add_record(item)
        # Use the HTTPFound function to perform a redirection back to the dashboard:
        request.session.flash('Record Submitted')
        redirect_url = request.route_url('env-dashboard')
        raise HTTPFound(redirect_url)
    return {
        'subtitle': 'Environment Access',
        'title': 'New Request'
    }

@view_config(route_name='env-request', renderer='self_service_portal:templates/env_access/env_existing_request.jinja2', permission='protected')
def env_request_view(request):
    # Find the ID required for the DynamoDB query:
    request_id = request.matchdict['id']
    # Create the connection to the DynamoDB table:
    region_name = request.registry.settings.get('dynamodb.region_name')
    table_name = request.registry.settings.get('dynamodb.table_name')
    dynamodb_service = DynamoDB(region_name, table_name)
    dynamodb_table = dynamodb_service.get_table()
    # Update the DynamoDB record when admin responds to a request:
    if request.method == "POST":
        # Specify the update expression and attribute values:
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
        # Update the item in the table:
        dynamodb_table.update_record(request_id, update_expression, expression_attribute_names, expression_attribute_values)
        # Create flash message to post back to page:
        request.session.flash('Record Updated')
    # Obtain the DynamoDB record required:
    response = dynamodb_table.query(
        KeyConditionExpression=Key('Request-ID').eq(request_id)
    )
    # Assign matched record data to a list:
    for item in response['Items']:
        first_name            = item.get('access-first-name')
        last_name             = item.get('access-last-name')
        email_address         = item.get('access-email-address')
        team                  = item.get('access-team')
        environment           = item.get('access-environment')
        status                = item.get('access-status')
        comments              = item.get('access-comments')
        request_date          = item.get('access-request-date')
        admin_name            = item.get('admin-full-name')
        admin_response_date   = item.get('admin-response-date')
        admin_comments        = item.get('admin-comments')
    # Pop the flash message up on return on HTTP POST:
    messages = request.session.pop_flash()
    return {
        'subtitle': 'Environment Access',
        'title': first_name + ' ' + last_name,
        'first_name': first_name,
        'last_name': last_name,
        'email_address': email_address,
        'team': team,
        'environment': environment,
        'status': status,
        'comments': comments,
        'request_date': request_date,
        'admin_name': admin_name,
        'admin_response_date': admin_response_date,
        'admin_comments': admin_comments,
        'message': messages
    }

@view_config(route_name='env-admin-control-panel', renderer='self_service_portal:templates/env_access/admin/request_control_panel.jinja2', permission='admin')
def env_admin_control_panel_view(request):
    # Find the ID required for the DynamoDB query:
    request_id = request.matchdict['id']
    # Create the connection to the DynamoDB table:
    region_name = request.registry.settings.get('dynamodb.region_name')
    table_name = request.registry.settings.get('dynamodb.table_name')
    dynamodb_service = DynamoDB(region_name, table_name)
    dynamodb_table = dynamodb_service.get_table()
    # When form is submitted:
    if request.method == "POST":
        # Specify the update expression and attribute values:
        form_data = request.params
        # Update Record:
        if form_data.get('AdminControlPanel') == "Update":
            # Specify the update expression and attribute values:
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
            # Update the item in the table:
            dynamodb_table.update_record(request_id, update_expression, expression_attribute_names, expression_attribute_values)
            # Create flash message to post back to page:
            request.session.flash('Record Updated')
        # Delete Record:
        if form_data.get('AdminControlPanel') == "Delete":
            # Delete the DynamoDB table record:
            dynamodb_table.delete_record(request_id)
            # Use the HTTPFound function to perform a redirection back to the dashboard:
            request.session.flash('Record Deleted')
            redirect_url = request.route_url('env-dashboard')
            raise HTTPFound(redirect_url)
    # Obtain the DynamoDB record required:
    response = dynamodb_table.query(
        KeyConditionExpression=Key('Request-ID').eq(request_id)
    )
    # Assign matched record data to a list:
    for item in response['Items']:
        first_name            = item.get('access-first-name')
        last_name             = item.get('access-last-name')
        email_address         = item.get('access-email-address')
        team                  = item.get('access-team')
        environment           = item.get('access-environment')
        status                = item.get('access-status')
        comments              = item.get('access-comments')
        request_date          = item.get('access-request-date')
        admin_name            = item.get('admin-full-name')
        admin_response_date   = item.get('admin-response-date')
        admin_comments        = item.get('admin-comments')
    # Pop the flash message up on return on HTTP POST:
    messages = request.session.pop_flash()
    return {
        'subtitle': 'Environment Access - Admin Control Panel',
        'title': first_name + ' ' + last_name + ' - Admin Control Panel',
        'first_name': first_name,
        'last_name': last_name,
        'email_address': email_address,
        'team': team,
        'environment': environment,
        'status': status,
        'comments': comments,
        'request_date': request_date,
        'admin_name': admin_name,
        'admin_response_date': admin_response_date,
        'admin_comments': admin_comments,
        'current_date_time': datetime.now().strftime("%d/%m/%Y %H:%M"),
        'message': messages
    }

@view_config(route_name='env-export-data', renderer='self_service_portal:templates/env_access/admin/export_data.jinja2', permission='admin')
def env_export_data_view(request):
    # Create the connection to the DynamoDB table:
    region_name = request.registry.settings.get('dynamodb.region_name')
    table_name = request.registry.settings.get('dynamodb.table_name')
    dynamodb_service = DynamoDB(region_name, table_name)
    dynamodb_table = dynamodb_service.get_table()
    # Get form data from the dashboard:
    form_data = request.params
    selected_status = form_data.get('status')
    selected_environment = form_data.get('environment')
    # Define condition expressions and attribute values based on the selected filters:
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
    # Perform a query to fetch records from DynamoDB with the conditions:
    if selected_status or selected_environment:
        scan_parameters['FilterExpression'] = status_condition
        scan_parameters['ExpressionAttributeNames'] = expression_attribute_names
        scan_parameters['ExpressionAttributeValues'] = expression_attribute_values
    try:
        response = dynamodb_table.scan(**scan_parameters)
    except Exception as e:
        raise HTTPNotFound from e
    # Extract the items and last evaluated key from the response:
    items = response.get('Items', [])
    # Arrange the records by status and request date:
    sorted_items = sorted(items, key=lambda x: ( x.get('access-status', ''), datetime.strptime(x.get('access-request-date'), '%d/%m/%Y %H:%M') ), reverse=True)
    # Get the number of requests for each status:
    status_type = ["Pending", "Approved", "Denied"]
    status_counts = {status: 0 for status in ['total_requests'] + [f'{status.lower()}_requests' for status in status_type]}
    for item in sorted_items:
        status_counts['total_requests'] += 1
        status = item.get('access-status')
        if status in status_type:
            status_counts[f'{status.lower()}_requests'] += 1
        else:
            # Increment all_requests even if status is not found:
            status_counts['all_requests'] += 1
    # When form is submitted - export results to CSV:
    if request.method == "POST":
        # Prepare CSV content:
        csv_content = env_export_data_view_post(sorted_items)
        # Set response headers for CSV download:
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
######################################################################################
######################################################################################
######################################################################################

@view_config(route_name='env-generate', renderer='self_service_portal:templates/env_generate/env_generate_url.jinja2', permission='protected')
def env_generate_view(request):
    approved_environments = get_approved_environments(request)
    return { 'subtitle': 'Environment URL\'s', 'title': 'Generate Environment URL', 'environments': approved_environments }

@view_config(route_name='env-update', renderer='self_service_portal:templates/env_generate/env_update_url.jinja2', permission='protected')
def env_update_view(request):
    return { 'subtitle': 'Environment URL\'s', 'title': 'Update URL\'s' }

######################################################################################
######################################################################################
######################################################################################
######################################################################################

def login_post_action(request):
    # Obtain values from form parameters:
    form_data = request.params
    email = form_data.get('emailAddress')
    password = form_data.get('password')
    # Add values to session:
    request.session['email_address'] = email
    # Check whether the user logging in is flagged for a force password change:
    cognito_instance = Cognito(request)
    password_check = cognito_instance.check_force_password_change_status()
    # Redirect the user if a password change is required:
    if password_check is True:
        redirect_url = request.route_url('change-password-force')
        raise HTTPFound(redirect_url)
    # Authenticate with Cognito if password check passes:
    if password_check is False:
        response = cognito_instance.handle_initiate_authentication(password)
        cognito_instance.handle_auth_response(response)

def change_password_force_post_action(request):
    # Obtain values from form parameters:
    form_data = request.params
    email = form_data.get('emailAddress')
    new_password = form_data.get('newPassword')
    # Add values to session:
    request.session['email_address'] = email
    # Confirm and reset Cognito password:
    cognito_instance = Cognito(request)
    cognito_instance.handle_force_password_change(new_password)
    # Use the HTTPFound function to perform a redirection to the change password screen:
    request.session.flash('Password Changed')
    redirect_url = request.route_url('login')
    raise HTTPFound(redirect_url)

def change_password_reset_request_post_action(request):
    # Obtain values from form parameters:
    form_data = request.params
    email = form_data.get('emailAddress')
    # Add values to session:
    request.session['email_address'] = email
    # Request Cognito password reset:
    cognito_instance = Cognito(request)
    cognito_instance.handle_password_reset_request()
    # Use the HTTPFound function to perform a redirection to the change password screen:
    redirect_url = request.route_url('change-password')
    raise HTTPFound(redirect_url)

def change_password_request_post_action(request):
    # Obtain values from form parameters:
    form_data = request.params
    email = form_data.get('emailAddress')
    new_password = form_data.get('newPassword')
    verification_code = form_data.get('verificationCode')
    # Add values to session:
    request.session['email_address'] = email
    # Confirm and reset Cognito password:
    cognito_instance = Cognito(request)
    cognito_instance.handle_password_reset(verification_code, new_password)
    # Use the HTTPFound function to perform a redirection to the change password screen:
    request.session.flash('Password Changed')
    redirect_url = request.route_url('login')
    raise HTTPFound(redirect_url)

def multi_factor_auth_setup_post_action(request):
    # Obtain values from form parameters:
    form_data = request.params
    verification_code = form_data.get('authVerificationCode')
    # Verify the MFA Setup & Update User Preferences:
    cognito_instance = Cognito(request)
    cognito_instance.handle_verify_software_token(request, verification_code)
    cognito_instance.handle_mfa_user_preferences()
    # Delete the QR code as it's no longer needed:
    os.remove(request.session['qr_code_path'])
    # Use the HTTPFound function to perform a redirection to the change password screen:
    request.session.flash('MFA Setup')
    redirect_url = request.route_url('login')
    raise HTTPFound(redirect_url)

def multi_factor_auth_verification_post_action(request):
    # Obtain values from form parameters:
    form_data = request.params
    verification_code = form_data.get('authVerificationCode')
    # Submit response to the MFA challenge:
    cognito_instance = Cognito(request)
    mfa_verification = cognito_instance.handle_respond_to_auth_challenge(request, verification_code)
    if mfa_verification["ChallengeParameters"] == {}:
        # Successful authentication, store user information in the session and redirect to the home page:
        headers = remember(request, request.session['email_address'])
        redirect_url = request.route_url('home')
        raise HTTPFound(redirect_url, headers=headers)

def env_export_data_view_post(data):
    # Create a CSV string from the sorted data:
    csv_content = ''
    if data:
        csv_content += ','.join(data[0].keys()) + '\n'
        for row in data:
            csv_content += ','.join(map(str, row.values())) + '\n'
    return csv_content

####################################################################################################
# TO DO LIST:
    # Work through the AWS App Runner workshop that's in Chrome favourites
    # Setup GitHub Actions pipeline to create AWS App Runner image off the back of the workshop
    # Keep the Update URL function in for now - setup API integration in futher issue down the line
    # Look to integrate ADFS Cognito into the application (maybe use hosted UI as evidence will be
    # there in GitHub for Cognito API for portfolio)
####################################################################################################

def get_approved_environments(request):
    # Create the connection to the DynamoDB table:
    region_name = request.registry.settings.get('dynamodb.region_name')
    table_name = request.registry.settings.get('dynamodb.table_name')
    dynamodb_service = DynamoDB(region_name, table_name)
    dynamodb_table = dynamodb_service.get_table()
    # Perform a query to fetch records from DynamoDB with the conditions:
    try:
        response = dynamodb_table.scan(FilterExpression=Attr('access-status').eq("Approved") & Key('access-email-address').eq(request.authenticated_userid))
    except Exception as e:
        raise HTTPNotFound from e
    # Extract the items and last evaluated key from the response:
    items = response.get('Items', [])
    # Arrange the records by status and request date:
    sorted_items = sorted(items, key=lambda x: ( x.get('access-environment') ))
    return sorted_items

####################################################################################################
