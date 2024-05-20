
import json
import boto3
from botocore.exceptions import ClientError
from pyramid.httpexceptions import HTTPNotFound

class Secrets:

    def __init__(self, region_name):

        """
        Summary:
            Initialize the Secrets Manager client with the specified AWS region.
        Args:
            region_name (str): The AWS region where the Secrets Manager client will be instantiated.
        """

        # Store the AWS region name:
        self.region_name = region_name
        # Initialize the Secrets Manager client with the specified region:
        self.client = boto3.client('secretsmanager', region_name=self.region_name)

    def get_secret(self, secret_name, secret_key):

        """
        Summary:
            Retrieves a specific secret key from AWS Secrets Manager.
        Args:
            secret_name (str): The name of the secret from which to retrieve the secret key.
            secret_key (str): The key of the secret data to retrieve.
        Returns:
            str: The value associated with the specified secret key.
        Raises:
            ClientError: If an error occurs during the retrieval process, it is raised to be handled by the caller.
        """

        try:
            # Retrieve the secret value from AWS Secrets Manager:
            get_secret_value_response = self.client.get_secret_value(
                SecretId=secret_name
            )
            if 'SecretString' in get_secret_value_response:
                # If the secret value is a string, parse it as JSON:
                secret_value = json.loads(get_secret_value_response["SecretString"])
            else:
                # If the secret value is binary, handle it accordingly:
                secret_value = get_secret_value_response['SecretBinary']
            # Return the value associated with the specified secret key:
            return secret_value[secret_key]
        except Exception as e:
            raise HTTPNotFound from e

    def update_secret(self, secret_name, secret_key, new_secret_value):

        """
        Summary:
            Updates a specific key/value pair in a secret stored in AWS Secrets Manager.
        Args:
            secret_name (str): The name or ARN of the secret.
            secret_key (str): The key whose value needs to be updated.
            new_secret_value (str): The new value to be assigned to the specified key.
        Raises:
            ClientError: If an error occurs while updating the secret.
        """

        try:
            # Retrieve the current secret value from AWS Secrets Manager:
            get_secret_value_response = self.client.get_secret_value(SecretId=secret_name)
            # Determine whether the secret value is a string or binary:
            if 'SecretString' in get_secret_value_response:
                current_secret_value = get_secret_value_response['SecretString']
            else:
                # Handle binary secrets if needed:
                current_secret_value = get_secret_value_response['SecretBinary']
            # Parse the current secret value as JSON and update the specified key with the new value:
            secret_dict = json.loads(current_secret_value)
            secret_dict[secret_key] = new_secret_value
            # Convert the updated dictionary back to a JSON string:
            updated_secret_value = json.dumps(secret_dict)
            # Update the secret in AWS Secrets Manager with the new value:
            self.client.update_secret(
                SecretId=secret_name,
                SecretString=updated_secret_value
            )
        except Exception as e:
            raise HTTPNotFound from e
