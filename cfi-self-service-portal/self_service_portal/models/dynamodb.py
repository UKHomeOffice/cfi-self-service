from pyramid.settings import asbool
import boto3

class Models:

    """ Functionality for database connections and manipulation """
    def get_dynamodb_connection(self):
        """ Returns DynamoDB table as object """
        dynamodb = boto3.resource('dynamodb', region_name= "eu-west-2")
        dynamodb_table_name = "Self-Service-Environment-Access-Requests"
        table = dynamodb.Table(dynamodb_table_name)
        return table
