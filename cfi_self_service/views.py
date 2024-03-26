
import uuid
from datetime import datetime
import math

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.view import notfound_view_config

from .backend.aws.dynamodb import DynamoDB
from .backend.models.access_request import Access_Request
from .backend.utils import get_status_counts, csv_data_export

##########################################################################################

@notfound_view_config(renderer='cfi_self_service:frontend/templates/not_found.jinja2')
def notfound_view(request):

    """
    Renders the view for handling not found (404) errors.
    This view is triggered when a route or resource is not found. It sets the response
    status to 404, retrieves the original exception causing the not found error, and renders
    the template for displaying the "Page Not Found" message along with the error details.

    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            It includes information such as subtitle, title, and error message.
    Example:
        This view is used to handle not found errors gracefully.
        It displays a custom error message along with details about the original exception.
    Note:
        - The view retrieves the original exception causing the not found error for logging or debugging purposes.
        - It sets the response status to 404 to indicate that the requested resource was not found.
        - The rendered template typically includes information to guide users on what to do next or who to contact.
    """

    # Retrieve the original exception causing the not found error:
    original_exception = request.exception.__cause__
    # Set the response status to 404:
    request.response.status = 404
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Page Not Found',
        'error_message': original_exception
    }

##########################################################################################

@view_config(route_name='home', renderer='cfi_self_service:frontend/templates/dashboard/home.jinja2')
def home_view(request):

    """
    Renders the home view of the CFI Self Service Portal.
    This view is the landing page of the CFI Self Service Portal. It renders the template
    for displaying the home page, which typically contains an overview of available features
    or quick links to different sections of the portal.

    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            It includes information such as subtitle and title for the home page.
    Example:
        This view is used as the landing page of the CFI Self Service Portal.
    """

    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Home'
    }

##########################################################################################

@view_config(route_name='access-requests-dashboard', renderer='cfi_self_service:frontend/templates/access_requests/dashboard.jinja2')
def access_requests_dashboard_view(request):

    """
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
    Example:
        This view is used to render the dashboard for managing access requests.
        It displays a paginated list of access requests, along with filtering options and status counts.
    Note:
        - The view extracts form data from the request to determine selected status and environment filters.
        - Results are sorted based on access status and request date.
        - Pagination is applied to the final set of results for better user experience.
    """

    # Obtain form data values:
    form_data = request.params
    selected_status = form_data.get('status')
    selected_environment = form_data.get('environment')
    # Perform DynamoDB table query to return list of records:
    dynamodb_table = DynamoDB("eu-west-2", "Self-Service-Environment-Access-Requests")
    response = dynamodb_table.scan_access_requests_table(selected_status, selected_environment)
    sorted_items = sorted(response, key=lambda x: (x.get('access-status', ''), datetime.strptime(x.get('access-request-date'), '%d/%m/%Y %H:%M')), reverse=True)
    # Get status counts based on returned results:
    status_counts = get_status_counts(sorted_items)
    # Setup pagination on the final set of results:
    page = int(request.params.get('page', 1))
    items_per_page = 10
    total_pages = math.ceil(len(sorted_items) / items_per_page)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_items = sorted_items[start_index:end_index]
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - Access Requests',
        'title': 'Dashboard',
        'result': paginated_items,
        'selected_status': selected_status,
        'selected_environment': selected_environment,
        'status_counts': status_counts,
        'page': page,
        'total_pages': total_pages
    }

@view_config(route_name='access-requests-new', renderer='cfi_self_service:frontend/templates/access_requests/new.jinja2')
def access_requests_new_view(request):

    """
    Handles the creation of a new access request for a specific environment.
    This view is triggered when a POST request is received. It extracts form data
    from the request, constructs an item representing the access request, and stores
    it in a DynamoDB table. After successful creation, the view redirects the user
    to the environment dashboard.

    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict: A dictionary containing data to be passed to the renderer for rendering the template.
            In this case, it includes 'subtitle' and 'title' for the template.
    Raises:
        HTTPFound: If the access request creation is successful, this exception is raised to redirect
            the user to the environment dashboard.
    Example:
        This view is used to render a form for creating a new access request.
        Upon form submission, it processes the request and redirects the user to the dashboard.
    Note:
        - The 'access-request-date' field is set to the current date and time.
        - The 'access-status' field is set to 'Pending' by default for a new request.
    """

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
        dynamodb_table = DynamoDB("eu-west-2", "Self-Service-Environment-Access-Requests")
        dynamodb_table.create_item(item)
        # Redirect user to the access requests dashboard:
        redirect_url = request.route_url('access-requests-dashboard')
        raise HTTPFound(redirect_url)
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - Access Requests',
        'title': 'New Request'
    }

@view_config(route_name='access-requests-existing', renderer='cfi_self_service:frontend/templates/access_requests/existing.jinja2')
def access_requests_existing_view(request):

    """
    Renders the view for an existing access request.
    This view retrieves information about a specific access request from the DynamoDB table,
    populates the Access_Request object with the retrieved data, and renders the template
    for displaying the details of the access request. It also handles updating the access request
    details based on admin input when a POST request is received.

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

    # Retrieve request ID from route parameters:
    request_id = request.matchdict['id']
    # Initialize DynamoDB instance and retrieve access request details:
    dynamodb_table = DynamoDB("eu-west-2", "Self-Service-Environment-Access-Requests")
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
            ':notification_alert': 'false',
        }
        # Update the item in DynamoDB with the provided information:
        dynamodb_table.update_item(request_id, update_expression, expression_attribute_names, expression_attribute_values)
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - Access Requests',
        'title': access_request_values.first_name + ' ' + access_request_values.last_name,
        'access_request': access_request_values
    }

@view_config(route_name='access-requests-admin', renderer='cfi_self_service:frontend/templates/access_requests/admin.jinja2')
def access_requests_admin_view(request):

    """
    Renders the view for administrative control panel of an access request.
    This view retrieves information about a specific access request from the DynamoDB table,
    populates the Access_Request object with the retrieved data, and renders the template
    for displaying the details of the access request along with administrative controls.
    It handles administrative actions such as updating and deleting access requests.

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

    # Retrieve request ID from route parameters:
    request_id = request.matchdict['id']
    # Initialize DynamoDB instance and retrieve access request details:
    dynamodb_table = DynamoDB("eu-west-2", "Self-Service-Environment-Access-Requests")
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
        # Handle delete action:
        if form_data.get('AdminControlPanel') == "Delete":
            dynamodb_table.delete_item(request_id)
            raise HTTPFound(request.route_url('access-requests-dashboard'))  # Redirect to environment dashboard after deletion
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - Access Requests - Admin Control Panel',
        'title': access_request_values.first_name + ' ' + access_request_values.last_name,
        'access_request': access_request_values,
        'current_date_time': datetime.now().strftime("%d/%m/%Y %H:%M")
    }

@view_config(route_name='access-requests-export', renderer='cfi_self_service:frontend/templates/access_requests/export.jinja2')
def access_requests_export_view(request):

    """
    Renders the view for exporting access request data.
    This view retrieves access request data from the DynamoDB table based on selected status
    and environment filters, sorts the data, calculates status counts, and renders the template
    for exporting the data in CSV format. It handles exporting data when a POST request is received.

    Args:
        request (Request): The Pyramid request object representing the HTTP request.
    Returns:
        dict or Response: If a GET request is received, returns a dictionary containing data to be passed
            to the renderer for rendering the template. If a POST request is received, returns a Response
            object containing the exported CSV data.
    Example:
        This view is used to export access request data in CSV format.
        Admin users can filter the data by status and environment before exporting it.
    Note:
        - Data is filtered based on selected status and environment filters.
        - Status counts are calculated based on the returned results.
        - When a POST request is received, the view exports the data in CSV format and returns a Response object.
    """

    # Initialize DynamoDB instance and retrieve access request details:
    dynamodb_table = DynamoDB("eu-west-2", "Self-Service-Environment-Access-Requests")
    # Extract form data values for status and environment filters:
    form_data = request.params
    selected_status = form_data.get('status')
    selected_environment = form_data.get('environment')
    # Query DynamoDB table and sort the results:
    response = dynamodb_table.scan_access_requests_table(selected_status, selected_environment)
    sorted_items = sorted(response, key=lambda x: (x.get('access-status', ''), datetime.strptime(x.get('access-request-date'), '%d/%m/%Y %H:%M')), reverse=True)
    # Get status counts based on returned results:
    status_counts = get_status_counts(sorted_items)
    # Handle POST request for exporting data:
    if request.method == "POST":
        # Export data in CSV format:
        csv_content = csv_data_export(sorted_items)
        csv_response = Response(content_type='text/csv')
        csv_response.content_disposition = 'attachment;filename=cfi_self_service_exported_data.csv'
        csv_response.text = csv_content
        return csv_response
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - Access Requests',
        'title': 'Export Data',
        'result': sorted_items,
        'selected_status': selected_status,
        'selected_environment': selected_environment,
        'status_counts': status_counts
    }

##########################################################################################

@view_config(route_name='environment-urls-generate', renderer='cfi_self_service:frontend/templates/environment_urls/generate.jinja2')
def environment_urls_generate_view(request):

    # Initialize DynamoDB instance and retrieve access request details:
    dynamodb_table = DynamoDB("eu-west-2", "Self-Service-Environment-Access-Requests")
    response = dynamodb_table.scan_for_approved_environments('Approved', 'ryan.jackson@digital.homeoffice.gov.uk')
    sorted_items = sorted(response, key=lambda x: ( x.get('access-environment') ))
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - Environment URLs',
        'title': 'Generate Environment URLs',
        'approved_environments': sorted_items
    }

@view_config(route_name='environment-urls-update', renderer='cfi_self_service:frontend/templates/environment_urls/update.jinja2')
def environment_urls_update_view(request):
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - Environment URLs',
        'title': 'Update Environment URLs'
    }

##########################################################################################

@view_config(route_name='vpn-profiles', renderer='cfi_self_service:frontend/templates/vpn_profiles/dashboard.jinja2')
def vpn_profiles_view(request):
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal - VPN Profiles',
        'title': 'Download VPN Profiles'
    }

##########################################################################################
