
import logging
import boto3

logger = logging.getLogger(__name__)

class DynamoDB:

    def __init__(self, region_name, table_name):
        self.region_name = region_name
        self.table_name = table_name
        self.connect()

    def connect(self):
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
        except Exception as e:
            logger.error(e)

    def get_table(self):
        try:
            self.table = self.dynamodb.Table(self.table_name)
            return self.table
        except Exception as e:
            logger.error(e)

    def add_record(self, item):
        try:
            self.table.put_item(Item=item)
        except Exception as e:
            logger.error(e)

    def update_record(self, request_id, update_expression, expression_attribute_names, expression_attribute_values):
        try:
            self.table.update_item(
                Key={
                    'Request-ID': request_id
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
        except Exception as e:
            logger.error(e)

    def delete_record(self, request_id):
        try:
            self.table.delete_item(Key={ 'Request-ID': request_id })
        except Exception as e:
            logger.error(e)
