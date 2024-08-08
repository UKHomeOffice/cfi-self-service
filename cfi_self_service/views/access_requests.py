from datetime import datetime
import uuid
import math
import os
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from cfi_self_service.backend.aws.dynamodb import DynamoDB
from cfi_self_service.backend.models.access_request import Access_Request
from cfi_self_service.backend.security.authentication import authenticated_view
from cfi_self_service.backend.utilities.access_requests import get_status_counts, csv_data_export

@view_config(route_name='access-requests-dashboard', renderer='cfi_self_service:frontend/templates/access_requests/dashboard.jinja2')
@authenticated_view
def access_requests_dashboard_view(request):

    """
    Summary:
        Renders the dashboard for managing access requests.
        This view handles displaying the dashboard, including filtering access requests by status
        and environment, querying the DynamoDB table, sorting the results, calculating status counts,
        setting up pagination, and rendering the template.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            It includes information such as subtitle, title, paginated items, selected status and environment,
            status counts, page number, and total number of pages.
    """

    # Load any flash messages that are available to display to the user:
    messages = request.session.pop_flash()
    # Perform a query to see if there are any outstanding notifications for the user:
    dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
    request_notifications = dynamodb_table.scan_for_request_notifications(request.session["email_address"])
    # Raise an alert on the navigation if notifications are unread:
    request_notifications_alert = False
    if request_notifications:
        request_notifications_alert = True
    # Obtain form data values:
    form_data = request.params
    selected_status = form_data.get('status')
    selected_environment = form_data.get('environment')
    # Perform DynamoDB table query to return list of records:
    dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
    response = dynamodb_table.scan_access_requests_table(selected_status, selected_environment)
    sorted_items = sorted(response, key=lambda x: ( x.get('access-status', ''), datetime.strptime(x.get('access-request-date'), '%d/%m/%Y %H:%M') ), reverse=True)
    # Get status counts based on returned results:
    status_counts = get_status_counts(sorted_items)
    # Setup pagination on the final set of results:
    items_per_page = 10
    page = int(request.params.get('page', 1))
    # Perform calculations on page numbers based on final set of results:
    total_pages = math.ceil(len(sorted_items) / items_per_page)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_items = sorted_items[start_index:end_index]
    # Handle POST request for exporting data:
    if request.method == "POST":
        # Get the current date and time as format as required:
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%d-%m-%Y-%H:%M")
        # Export data in CSV format:
        csv_content = csv_data_export(sorted_items)
        csv_response = Response(content_type='text/csv')
        csv_response.content_disposition = f'attachment;filename=cfi_self_service_exported_data_{formatted_datetime}.csv'
        csv_response.text = csv_content
        return csv_response
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Access Requests',
        'admin_user': request.session["admin_user"],
        'notifications_alert_show': request_notifications_alert,
        'notifications': request_notifications,
        'message': messages,
        'result': paginated_items,
        'selected_status': selected_status,
        'selected_environment': selected_environment,
        'status_counts': status_counts,
        'page': page,
        'total_pages': total_pages
    }

@view_config(route_name='access-requests-new', renderer='cfi_self_service:frontend/templates/access_requests/new.jinja2')
@authenticated_view
def access_requests_new_view(request):

    """
    Summary:
        Handles the creation of a new access request for a specific environment.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            In this case, it includes 'subtitle' and 'title' for the template.
    Example:
        This view is used to render a form for creating a new access request.
        Upon form submission, it processes the request and redirects the user to the dashboard.
    Note:
        - The 'access-request-date' field is set to the current date and time.
        - The 'access-status' field is set to 'Pending' by default for a new request.
    """

    # Perform a query to see if there are any outstanding notifications for the user:
    dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
    request_notifications = dynamodb_table.scan_for_request_notifications(request.session["email_address"])
    # Raise an alert on the navigation if notifications are unread:
    request_notifications_alert = False
    if request_notifications:
        request_notifications_alert = True

    if request.method == "POST":
        # Extract form data from the request:
        form_data = request.params
        # Construct item representing the access request:
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
        # Initialize DynamoDB instance and create the item:
        dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
        dynamodb_table.create_item(item)
        # Redirect user to the access requests dashboard:
        request.session.flash('Record Submitted')
        redirect_url = request.route_url('access-requests-dashboard')
        raise HTTPFound(redirect_url)
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - Access Requests',
        'title': 'New Request',
        'notifications_alert_show': request_notifications_alert,
        'notifications': request_notifications,
    }

@view_config(route_name='access-requests-existing', renderer='cfi_self_service:frontend/templates/access_requests/existing.jinja2')
@authenticated_view
def access_requests_existing_view(request):

    """
    Summary:
        Renders the view for an existing access request.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            It includes information such as subtitle, title, and details of the access request.
    Example:
        This view is used to render the details of an existing access request.
        It displays the access request details fetched from the DynamoDB table and allows
        admin users to update the status and provide comments.
    Note:
        - The view retrieves the request ID from the route parameters to identify the specific access request.
        - The view constructs an Access_Request object to hold the access request details.
        - Admin users can update the access request status and provide comments via a form submission.
    """

    # Perform a query to see if there are any outstanding notifications for the user:
    dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
    request_notifications = dynamodb_table.scan_for_request_notifications(request.session["email_address"])
    # Raise an alert on the navigation if notifications are unread:
    request_notifications_alert = False
    if request_notifications:
        request_notifications_alert = True
    # Retrieve request ID from route parameters:
    request_id = request.matchdict['id']
    # Initialize DynamoDB instance and retrieve access request details:
    dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
    response = dynamodb_table.get_item(request_id)
    # Initialize Access_Request object to hold access request details:
    access_request_values = None
    # Extract and populate Access_Request object with retrieved data:
    for item in response['Items']:
        access_request_values = Access_Request(
            item.get('access-first-name'),
            item.get('access-last-name'),
            item.get('access-email-address'),
            item.get('access-team'),
            item.get('access-environment'),
            item.get('access-status'),
            item.get('access-comments'),
            item.get('access-request-date'),
            item.get('admin-full-name'),
            item.get('admin-response-date'),
            item.get('admin-comments')
        )
    # Handle POST request for updating access request details:
    if request.method == "POST":
        # Extract form data from the request:
        form_data = request.params
        # Define update expression and attribute values for updating the item in DynamoDB:
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
            ':admin_form_full_name': 'Ryan Jackson',  # Assuming admin's full name is hardcoded
            ':admin_form_response_date': datetime.now().strftime("%d/%m/%Y %H:%M"),
            ':notification_alert': 'true',
        }
        # Update the item in DynamoDB with the provided information:
        dynamodb_table.update_item(request_id, update_expression, expression_attribute_names, expression_attribute_values)
        # Redirect user to the access requests dashboard:
        request.session.flash('Record Updated')
        redirect_url = request.route_url('access-requests-dashboard')
        raise HTTPFound(redirect_url)
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - Access Requests',
        'title': access_request_values.first_name + ' ' + access_request_values.last_name,
        'admin_user': request.session["admin_user"],
        'access_request': access_request_values,
        'notifications_alert_show': request_notifications_alert,
        'notifications': request_notifications
    }

@view_config(route_name='access-requests-admin', renderer='cfi_self_service:frontend/templates/access_requests/admin.jinja2')
@authenticated_view
def access_requests_admin_view(request):

    """
    Summary:    
        Renders the view for administrative control panel of an access request.
    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            It includes information such as subtitle, title, access request details, and current date-time.
    Example:
        This view is used by administrators to manage access requests.
        It allows administrators to update access request details and delete access requests as needed.
    Note:
        - The view retrieves the request ID from the route parameters to identify the specific access request.
        - The view constructs an Access_Request object to hold the access request details.
        - Admin controls such as update and delete actions are handled based on form submission.
    """

    if (request.session["admin_user"] is True):
        # Perform a query to see if there are any outstanding notifications for the user:
        dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
        request_notifications = dynamodb_table.scan_for_request_notifications(request.session["email_address"])
        # Raise an alert on the navigation if notifications are unread:
        request_notifications_alert = False
        if request_notifications:
            request_notifications_alert = True
        # Retrieve request ID from route parameters:
        request_id = request.matchdict['id']
        # Initialize DynamoDB instance and retrieve access request details:
        dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
        response = dynamodb_table.get_item(request_id)
        # Initialize Access_Request object to hold access request details:
        access_request_values = None
        # Extract and populate Access_Request object with retrieved data:
        for item in response['Items']:
            access_request_values = Access_Request(
                item.get('access-first-name'),
                item.get('access-last-name'),
                item.get('access-email-address'),
                item.get('access-team'),
                item.get('access-environment'),
                item.get('access-status'),
                item.get('access-comments'),
                item.get('access-request-date'),
                item.get('admin-full-name'),
                item.get('admin-response-date'),
                item.get('admin-comments')
            )
        # Handle POST request for administrative actions:
        if request.method == "POST":
            form_data = request.params
            # Handle update action:
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
                    ':admin_full_name': 'Ryan Jackson',  # Assuming admin's full name is hardcoded
                    ':admin_comments': form_data.get('adminComments'),
                    ':admin_response_date': datetime.now().strftime("%d/%m/%Y %H:%M"),
                    ':notification_alert': 'false',
                }
                dynamodb_table.update_item(request_id, update_expression, expression_attribute_names, expression_attribute_values)    
                request.session.flash('Record Updated')
            # Handle delete action:
            if form_data.get('AdminControlPanel') == "Delete":
                dynamodb_table.delete_item(request_id)
                request.session.flash('Record Deleted')
            raise HTTPFound(request.route_url('access-requests-dashboard'))  # Redirect to environment dashboard after deletion
        # Return data for rendering the template:
        return {
            'subtitle': 'CFI Self Service Portal - Access Requests - Admin Control Panel',
            'title': access_request_values.first_name + ' ' + access_request_values.last_name,
            'notifications_alert_show': request_notifications_alert,
            'notifications': request_notifications,
            'access_request': access_request_values,
            'current_date_time': datetime.now().strftime("%d/%m/%Y %H:%M")
        }
    else:
        # Redirect user to the access requests dashboard:
        redirect_url = request.route_url('access-requests-dashboard')
        raise HTTPFound(redirect_url)
