
import boto3
from boto3.dynamodb.conditions import Key, Attr
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

class DynamoDB:

    def __init__(self, region_name, table_name):

        """
        Summary:
            A class to handle the connection and manipulation of DynamoDB tables.
        Args:
            table_name (str): The name of the DynamoDB table.
            region_name (str): The AWS region where the DynamoDB table is located.
        """

        self.region_name = region_name
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def create_item(self, item):

        """
        Summary:
            Creates a new item in the DynamoDB table.
        Args:
            item (dict): The item to be created in the DynamoDB table.
                         Should be a dictionary representing the item attributes.
        """

        try:
            self.table.put_item(Item=item)
        except Exception as e:
            raise HTTPNotFound from e

    def get_item(self, key):

        """
        Summary:
            Retrieves an item from the DynamoDB table based on the provided key.
        Args:
            key (dict): The primary key of the item to be retrieved.
                        Should be a dictionary representing the primary key attributes.
        Returns:
            dict: The retrieved item if found, otherwise None.
        """

        try:
            response = self.table.query(KeyConditionExpression=Key('Request-ID').eq(key))
            if response:
                return response
        except Exception as e:
            raise HTTPNotFound from e

    def update_item(self, key, update_expression, expression_attribute_names, expression_attribute_values):
    
        """
        Summary:
                Updates an item in the DynamoDB table.
        Args:
            key (dict): The primary key of the item to be updated.
                        Should be a dictionary representing the primary key attributes.
            update_expression (str): The update expression to be applied to the item.
            expression_attribute_values (dict): A dictionary containing attribute values used in the update expression.
        """

        try:
            self.table.update_item(
                Key={ 'Request-ID': key },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
        except Exception as e:
            raise HTTPNotFound from e

    def delete_item(self, key):

        """
        Summary:
            Deletes an item from the DynamoDB table.
        Args:
            key (dict): The primary key of the item to be deleted.
                        Should be a dictionary representing the primary key attributes.
        """

        try:
            self.table.delete_item(Key={ 'Request-ID': key })
        except Exception as e:
            raise HTTPNotFound from e

    def scan_access_requests_table(self, selected_status=None, selected_environment=None):

        """
        Summary:
            Scans the DynamoDB table and returns items based on selected status and environment.
        Args:
            selected_status (str, optional): The selected status to filter items by.
                Defaults to None.
            selected_environment (str, optional): The selected environment to filter items by.
                Defaults to None.
        Returns:
            list: A list containing items matching the filter criteria, if any.
                If no items match the criteria, an empty list is returned.
        Note:
            - The method supports filtering by both status and environment independently or in combination.
            - If no filters are applied (i.e., both selected_status and selected_environment are None),
            the method will return all items in the DynamoDB table.
        """

        try:
            status_condition = None
            environment_condition = None
            scan_parameters = {}
            expression_attribute_names = {}
            expression_attribute_values = {}
            # Construct filter conditions based on selected status and environment:
            if selected_status:
                status_condition = '#access_status = :status'
                expression_attribute_names['#access_status'] = 'access-status'
                expression_attribute_values[':status'] = selected_status
            if selected_environment:
                environment_condition = '#access_environment = :environment'
                if status_condition:
                    status_condition = status_condition + ' AND ' + environment_condition
                else:
                    status_condition = environment_condition
                expression_attribute_names['#access_environment'] = 'access-environment'
                expression_attribute_values[':environment'] = selected_environment
            # Add filter expression to scan parameters:
            if selected_status or selected_environment:
                scan_parameters['FilterExpression'] = status_condition
                scan_parameters['ExpressionAttributeNames'] = expression_attribute_names
                scan_parameters['ExpressionAttributeValues'] = expression_attribute_values
            # Perform the scan operation:
            response = self.table.scan(**scan_parameters)
            # Extract items from the response:
            return response.get('Items', [])
        except Exception as e:
            raise HTTPNotFound from e

    def scan_for_approved_environments(self, status=None, user=None):

        """
        Summary:
            Scans the DynamoDB table to retrieve approved environments for a specific user.
            This method performs a scan operation on the DynamoDB table to retrieve items that match
            the specified status and user email address. It filters the items based on the access status
            and the user's email address.
        Args:
            status (str, optional): The status of the access request. Defaults to None.
            user (str, optional): The email address of the user for whom approved environments are scanned. Defaults to None.
        Returns:
            list: A list containing items representing approved environments for the specified user.
        Note:
            - The method expects the 'status' and 'user' parameters to be provided to filter the results.
            - The method returns a list of items representing approved environments for the specified user.
        """

        try:
            # Perform the scan operation with filtering by access status and user email address:
            response = self.table.scan(FilterExpression=Attr('access-status').eq(status) & Key('access-email-address').eq(user))
            # Extract items from the response:
            return response.get('Items', [])
        except Exception as e:
            raise HTTPNotFound from e

    def scan_for_request_notifications(self, user=None):

        """
        Summary:
            Scans the DynamoDB table to retrieve request notifications for a specific user.
            This method performs a scan operation on the DynamoDB table to retrieve items that match
            the whether the notification alert field is true and user email address.
        Args:
            status (str, optional): The status of the access request. Defaults to None.
            user (str, optional): The email address of the user for whom approved environments are scanned. Defaults to None.
        Returns:
            list: A list containing items representing approved environments for the specified user.
        Note:
            - The method expects the 'status' and 'user' parameters to be provided to filter the results.
            - The method returns a list of items representing approved environments for the specified user.
        """

        try:
            # Perform the scan operation with filtering by access status and user email address:
            response = self.table.scan(FilterExpression=Attr('notification-alert').eq("true") & Key('access-email-address').eq(user))
            # Extract items from the response:
            return response.get('Items', [])
        except Exception as e:
            raise HTTPNotFound from e
