
import math
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from ..models.dynamodb import Models

@view_config(route_name='home', renderer='self_service_portal:templates/home.jinja2')
def home_view(request):
    return {
        'subtitle': 'Self Service Portal',
        'title': 'Welcome'
    }

########################################################################################################################
# Environment Access - Dashboard:
########################################################################################################################

@view_config(route_name='env-dashboard', renderer='self_service_portal:templates/env_access/env_dashboard.jinja2')
def env_dashboard_view(request):

    # Pop the flash message up on return on HTTP POST:
    messages = request.session.pop_flash()

    # Create the connection to the DynamoDB table:
    dynamodb_table = Models.get_dynamodb_connection("")

    # Get form data from the dashboard:
    form_data = request.params
    selected_status = form_data.get('status')
    selected_environment = form_data.get('environment')

    # Define condition expressions and attribute values based on the selected filters:
    condition_expression = None
    environment_condition = None
    scan_parameters = {}
    expression_attribute_names = {}
    expression_attribute_values = {}

    if selected_status:
        condition_expression = '#access_status = :status'
        expression_attribute_names['#access_status'] = 'access-status'
        expression_attribute_values[':status'] = selected_status
    if selected_environment:
        environment_condition = '#access_environment = :environment'
        if condition_expression :
            condition_expression = condition_expression + ' AND ' + environment_condition
        else:
            condition_expression = environment_condition
        expression_attribute_names['#access_environment'] = 'access-environment'
        expression_attribute_values[':environment'] = selected_environment

    # Perform a query to fetch records from DynamoDB with the conditions:
    if selected_status or selected_environment:
        scan_parameters['FilterExpression'] = condition_expression
        scan_parameters['ExpressionAttributeNames'] = expression_attribute_names
        scan_parameters['ExpressionAttributeValues'] = expression_attribute_values

    response = dynamodb_table.scan(**scan_parameters)

    # Extract the items and last evaluated key from the response:
    # Then, arrange the records by status and request date:
    items = response.get('Items', [])
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

########################################################################################################################
# Environment Access - New Request:
########################################################################################################################

@view_config(route_name='env-new-request', renderer='self_service_portal:templates/env_access/env_new_request.jinja2')
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
        dynamodb_table = Models.get_dynamodb_connection("")
        dynamodb_table.put_item(
            Item=item
        )
        # Use the HTTPFound exception to perform a redirection back to the dashboard:
        request.session.flash('Record Submitted')
        redirect_url = request.route_url('env-dashboard')
        raise HTTPFound(redirect_url)

    return {
        'subtitle': 'Environment Access',
        'title': 'New Request'
    }

########################################################################################################################
# Environment Access - Existing Request:
########################################################################################################################

@view_config(route_name='env-request', renderer='self_service_portal:templates/env_access/env_existing_request.jinja2')
def env_request_view(request):
    # Find the ID required for the DynamoDB query:
    request_id = request.matchdict['id']
    # Connect to the DynamoDB table:
    dynamodb_table = Models.get_dynamodb_connection("")
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
        dynamodb_table.update_item(
            Key={
                'Request-ID': request_id,
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
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

########################################################################################################################
# Environment Access - Admin Control Panel:
########################################################################################################################

@view_config(route_name='env-admin-control-panel', renderer='self_service_portal:templates/env_access/admin/admin_actions.jinja2')
def env_admin_control_panel_view(request):

    # Find the ID required for the DynamoDB query:
    request_id = request.matchdict['id']
    # Connect to the DynamoDB table:
    dynamodb_table = Models.get_dynamodb_connection("")

    if request.method == "POST":
        # Specify the update expression and attribute values:
        form_data = request.params
        # Update Record:
        if form_data.get('AdminControlPanel') == "Update":
            # Specify the update expression and attribute values:
            form_data = request.params
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
            dynamodb_table.update_item(
                Key={
                    'Request-ID': request_id
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
            # Create flash message to post back to page:
            request.session.flash('Record Updated')
        # Delete Record:
        if form_data.get('AdminControlPanel') == "Delete":
            # Delete the DynamoDB table record:
            response = dynamodb_table.delete_item(
                Key={
                    'Request-ID': request_id
                }
            )
            # Create flash message to post back to page:
            request.session.flash('Record Deleted')
            # Use the HTTPFound exception to perform a redirection back to the dashboard:
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
