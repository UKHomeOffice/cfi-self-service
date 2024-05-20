
import boto3
import pytest
from cfi_self_service.backend.aws.secrets import Secrets

@pytest.mark.integ
def test_scenario():

    # Retrieve secrets from AWS Secrets Manager:
    region_name = "eu-west-2"
    secrets_instance = Secrets(region_name)
    secret = secrets_instance.get_secret("")
    assert secret
