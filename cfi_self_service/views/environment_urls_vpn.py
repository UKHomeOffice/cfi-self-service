
import os
from datetime import datetime
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from cfi_self_service.backend.aws.dynamodb import DynamoDB
from cfi_self_service.backend.aws.secrets import Secrets
from cfi_self_service.backend.security.authentication import authenticated_view

@view_config(route_name='environment-urls-vpn-generate', renderer='cfi_self_service:frontend/templates/environment_urls_vpn/generate.jinja2')
@authenticated_view
def environment_urls_vpn_generate_view(request):

    """
    Summary:
        View for generating environment URLs and VPN profiles for approved environments.
    Args:
        request: The Pyramid request object.
    Returns:
        dict: A dictionary containing the subtitle, title, and approved environments to be rendered in the template.
    """

    # Initialise DynamoDB instance and retrieve access request details:
    dynamodb_table = DynamoDB(os.environ.get('REGION_NAME'), os.environ.get('DYNAMO_DB_ACCESS_REQUESTS_TABLE_NAME'))
    response = dynamodb_table.scan_for_approved_environments('Approved', request.session["email_address"])
    order = { "Test": 0, "Development": 1, "Production": 2 }
    sorted_items = sorted(response, key=lambda x: order.get(x.get('access-environment'), float('inf')))
    # Retrieve environment URL's from Secrets Manager:
    region_name = os.environ.get('REGION_NAME')
    secrets_instance = Secrets(region_name)
    # Map environments to their secret names and keys:
    environment_secrets = {
        "Test": {
            "name": os.environ.get('DEA_TEST_ENVIRONMENT_URL_NAME'),
            "key": os.environ.get('DEA_TEST_ENVIRONMENT_URL_KEY')
        },
        "Development": {
            "name": os.environ.get('DEA_DEV_ENVIRONMENT_URL_NAME'),
            "key": os.environ.get('DEA_DEV_ENVIRONMENT_URL_KEY')
        },
        "Production": {
            "name": os.environ.get('DEA_PROD_ENVIRONMENT_URL_NAME'),
            "key": os.environ.get('DEA_PROD_ENVIRONMENT_URL_KEY')
        }
    }
    # Loop through each approved request and set the corresponding environment URLs:
    for item in sorted_items:
        # Check if the access environment exists in the environment_secrets dictionary
        access_environment = item.get('access-environment')
        if access_environment in environment_secrets:
            # Retrieve the corresponding secret information (name and key) for the access environment:
            secret_info = environment_secrets[access_environment]
            environment_url = secrets_instance.get_secret(secret_info['name'], secret_info['key'])
            # Add the retrieved environment URL to the current item under the key 'environment_url':
            item['access-environment-url'] = environment_url
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Environment URLs & VPN Profiles',
        'approved_environments': sorted_items,
    }

@view_config(route_name='environment-urls-vpn-update', renderer='cfi_self_service:frontend/templates/environment_urls_vpn/update.jinja2')
@authenticated_view
def environment_urls_vpn_update_view(request):

    """
    Summary:
        Handles the updating of environment URLs for VPN configuration. This view displays current 
        environment URLs retrieved from AWS Secrets Manager and updates the URLs if they have
        changed upon form submission.
    Args:
        request (Request): The request object containing HTTP request data.
    Returns:
        dict: Data for rendering the template if GET method.
        HTTPFound: Redirect to the same page with a success message if POST method.
    """

    # Load any flash messages that are available to display to the user:
    messages = request.session.pop_flash()
    # Pull through the environment URLs from Secrets Manager:
    region_name = os.environ.get('REGION_NAME')
    secrets_instance = Secrets(region_name)
    dea_test_environment_url = secrets_instance.get_secret(os.environ.get('DEA_TEST_ENVIRONMENT_URL_NAME'), os.environ.get('DEA_TEST_ENVIRONMENT_URL_KEY'))
    dea_dev_environment_url = secrets_instance.get_secret(os.environ.get('DEA_DEV_ENVIRONMENT_URL_NAME'), os.environ.get('DEA_DEV_ENVIRONMENT_URL_KEY'))
    dea_prod_environment_url = secrets_instance.get_secret(os.environ.get('DEA_PROD_ENVIRONMENT_URL_NAME'), os.environ.get('DEA_PROD_ENVIRONMENT_URL_KEY'))
    # Update the secrets if the values have changed on POST:
    if request.method == "POST":
        # Extract form data from the request:
        form_data = request.params
        form_dea_test_environment_url = form_data.get('deaTestEnvironmentURL')
        form_dea_dev_environment_url = form_data.get('deaDevEnvironmentURL')
        form_dea_prod_environment_url = form_data.get('deaProdEnvironmentURL')
        # Update the test secret if the value has changed:
        if (form_dea_test_environment_url != dea_test_environment_url):
            secrets_instance.update_secret(os.environ.get('DEA_TEST_ENVIRONMENT_URL_NAME'), os.environ.get('DEA_TEST_ENVIRONMENT_URL_KEY'), form_dea_test_environment_url)
        # Update the dev secret if the value has changed:
        if (form_dea_dev_environment_url != dea_dev_environment_url):
            secrets_instance.update_secret(os.environ.get('DEA_DEV_ENVIRONMENT_URL_NAME'), os.environ.get('DEA_DEV_ENVIRONMENT_URL_KEY'), form_dea_dev_environment_url)
        # Update the prod secret if the value has changed:
        if (form_dea_prod_environment_url != dea_prod_environment_url):
            secrets_instance.update_secret(os.environ.get('DEA_PROD_ENVIRONMENT_URL_NAME'), os.environ.get('DEA_PROD_ENVIRONMENT_URL_KEY'), form_dea_prod_environment_url)
        # Redirect user to the access requests dashboard:
        request.session.flash('Environment URLs Updated')
        redirect_url = request.route_url('environment-urls-vpn-update')
        raise HTTPFound(redirect_url)
    # Return data for rendering the template:
    return {
        'subtitle': 'CFI Self Service Portal',
        'title': 'Update Environment URLs',
        'message': messages,
        'dea_test_environment_url': dea_test_environment_url,
        'dea_dev_environment_url': dea_dev_environment_url,
        'dea_prod_environment_url': dea_prod_environment_url
    }
