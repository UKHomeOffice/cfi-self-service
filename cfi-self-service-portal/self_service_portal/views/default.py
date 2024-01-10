
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

@view_config(route_name='env-dashboard', renderer='self_service_portal:templates/env_access/env_dashboard.jinja2')
def env_dashboard_view(request):
    # Pop the flash message up on return on HTTP POST:
    messages = request.session.pop_flash()
    # Create the connection to the DynamoDB table:
    dynamodb_table = Models.get_dynamodb_connection("")
    response = dynamodb_table.scan()
    items = response.get('Items', [])
    # Setup integers to hold status counts:
    all_requests_count = 0
    pending_requests = 0
    approved_requests = 0
    denied_requests = 0
    # Get the counts for each request status:
    for item in items:
        all_requests_count += 1
        if item.get('access-status') == "Pending":
            pending_requests += 1
        elif item.get('access-status') == "Approved":
            approved_requests += 1
        elif item.get('access-status') == "Denied":
            denied_requests += 1
    return {
        'subtitle': 'Environment Access',
        'title': 'Dashboard',
        'message': messages,
        'result': items,
        'totalCount': all_requests_count,
        'pendingCount': pending_requests,
        'approvedCount': approved_requests,
        'deniedCount': denied_requests
    }

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
        # Create the connection to the DynamoDB table:
        dynamodb_table = Models.get_dynamodb_connection("")
        # Add the new request record to the DynamoDB table:
        dynamodb_table.put_item(
            Item=item
        )
        # Use the HTTPFound exception to perform a redirection back to the dashboard:
        request.session.flash('Thanks for your request!')
        redirect_url = request.route_url('env-dashboard')
        raise HTTPFound(redirect_url)
    return {
        'subtitle': 'Environment Access',
        'title': 'New Request'
    }

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
        update_expression = "SET #access_status = :access_form_status, #admin_comments = :admin_form_comments, #admin_full_name = :admin_form_full_name, #admin_response_date = :admin_form_response_date"
        expression_attribute_names = {
            '#access_status': 'access-status',
            '#admin_comments': 'admin-comments',
            '#admin_full_name': 'admin-full-name',
            '#admin_response_date': 'admin-response-date'
        }
        expression_attribute_values = {
            ':access_form_status': form_data.get('adminStatus'),
            ':admin_form_comments': form_data.get('adminComments'),
            ':admin_form_full_name': 'Ryan Jackson',
            ':admin_form_response_date': datetime.now().strftime("%d/%m/%Y %H:%M")
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
        request.session.flash('Thanks for actioning this request!')
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
