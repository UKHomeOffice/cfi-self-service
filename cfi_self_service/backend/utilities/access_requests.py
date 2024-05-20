
def get_status_counts(sorted_items):

    """
    Summary:
        Calculates the count of requests based on their status.
    Args:
        sorted_items (list): A list of dictionaries representing individual requests.
            Each dictionary should contain a key 'access-status' indicating the status of the request.
    Returns:
        dict: A dictionary containing counts of requests for different status types.
            Keys represent the status type, and values represent the count of requests for that status type.
    Note:
        The 'all_requests' count represents the number of requests with statuses other than 'Pending', 'Approved', or 'Denied'.
    """

    # Define the status types:
    status_type = ["Pending", "Approved", "Denied"]
    # Initialize counts for different status types:
    status_counts = {status: 0 for status in ['total_requests'] + [f'{status.lower()}_requests' for status in status_type]}
    # Iterate through sorted_items and update counts:
    for item in sorted_items:
        status_counts['total_requests'] += 1
        status = item.get('access-status')
        if status in status_type:
            status_counts[f'{status.lower()}_requests'] += 1
        else:
            status_counts['all_requests'] += 1
    return status_counts

def csv_data_export(sorted_items):

    """
    Summary:
        Export data in CSV format.
    Args:
        data (list of dict): A list of dictionaries representing rows of data.
    Returns:
        str: A string containing the data in CSV format.
    Example:
        This function is used to export data in CSV format, such as access request details.
    Note:
        - The function checks if the input data list is not empty before processing.
        - It constructs the CSV content by joining keys of the first dictionary (column headers)
          with commas and appending a newline character.
        - It then iterates over each dictionary in the list, joins the values with commas,
          and appends a newline character to form each row.
    """

    csv_content = ''
    if sorted_items:
        # Construct CSV header with column names:
        csv_content += ','.join(sorted_items[0].keys()) + '\n'
        # Add rows of data:
        for row in sorted_items:
            csv_content += ','.join(map(str, row.values())) + '\n'
    return csv_content
