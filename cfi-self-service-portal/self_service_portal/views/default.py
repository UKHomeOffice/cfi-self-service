
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
        'title': 'Welcome',
    }

@view_config(route_name='env-dashboard', renderer='self_service_portal:templates/env_access/env_dashboard.jinja2')
def env_dashboard_view(request):
    dynamodb_table = Models.get_dynamodb_connection("")
    response = dynamodb_table.scan()
    items = response.get('Items', [])
    return {
        'title': 'Request Environment Access',
        'result': items
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

    return {
        'title': 'New Environment Access Request',
    }

@view_config(route_name='env-request', renderer='self_service_portal:templates/env_access/env_existing_request.jinja2')
def env_request_view(request):

    # Find the ID required for the DynamoDB query:
    request_id = request.matchdict['id']

    # Connect to the DynamoDB table and obtain the record required:
    dynamodb_table = Models.get_dynamodb_connection("")
    response = dynamodb_table.query(
        KeyConditionExpression=Key('Request-ID').eq(request_id)
    )

    # Assign matched record data to a list:
    for item in response['Items']:
        first_name            = item.get('access-first-name')
        last_name             = item.get('access-last-name')
        team                  = item.get('access-team')
        environment           = item.get('access-environment')
        status                = item.get('access-status')
        request_date          = item.get('access-request-date')
        admin_name            = item.get('admin-full-name')
        admin_response_date   = item.get('admin-response-date')
        admin_comments        = item.get('admin-comments')

    return {
        'title': first_name + ' ' + last_name + ' - Environment Access Request',
        'first_name': first_name,
        'last_name': last_name,
        'team': team,
        'environment': environment,
        'status': status,
        'request_date': request_date,
        'admin_name': admin_name,
        'admin_response_date': admin_response_date,
        'admin_comments': admin_comments
    }
