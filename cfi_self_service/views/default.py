
import os
from pyramid.view import view_config
from cfi_self_service.backend.security.authentication import authenticated_view
from cfi_self_service.backend.aws.dynamodb import DynamoDB

@view_config(route_name='home', renderer='cfi_self_service:frontend/templates/dashboard/home.jinja2')
@authenticated_view
def home_view(request):

    """
    Summary:
        This view is the landing page of the CFI Self Service Portal. It renders the template
        for displaying the home page, which contains an overview of available features
        or quick links to different sections of the portal.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            It includes information such as subtitle and title for the home page.
    """

    # Perform a query to see if there are any outstanding notifications for the user:
    dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
    request_notifications = dynamodb_table.scan_for_request_notifications(request.session["email_address"])
    # Raise an alert on the navigation if notifications are unread:
    request_notifications_alert = False
    if request_notifications:
        request_notifications_alert = True
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Home',
        'notifications_alert_show': request_notifications_alert,
        'notifications': request_notifications
    }
