
from dataclasses import dataclass

@dataclass
class Access_Request:
 
    """
    Summary:
        Represents an access request entry. This data class represents an access request entry 
        with various attributes such as first name, last name, email address, team, environment, 
        status, comments, request date, admin name, admin response date, and admin comments.
    Attributes:
        first_name (str): The first name of the requester.
        last_name (str): The last name of the requester.
        email_address (str): The email address of the requester.
        team (str): The team associated with the access request.
        environment (str): The environment for which access is requested.
        status (str): The status of the access request (e.g., pending, approved, denied).
        comments (str): Comments associated with the access request.
        request_date (str): The date and time when the access request was made.
        admin_name (str): The name of the administrator handling the access request.
        admin_response_date (str): The date and time of the administrator's response to the request.
        admin_comments (str): Comments provided by the administrator.
    Example:
        This class is used to represent individual access request entries in a system.
        It can be instantiated with appropriate values for each attribute to represent a specific access request.
    Note:
        - This class is decorated with the @dataclass decorator, which automatically generates
          special methods such as __init__(), __repr__(), and __eq__() based on the defined attributes.
    """

    first_name: str
    last_name: str
    email_address: str
    team: str
    environment: str
    status: str
    comments: str
    request_date: str
    admin_name: str
    admin_response_date: str
    admin_comments: str
