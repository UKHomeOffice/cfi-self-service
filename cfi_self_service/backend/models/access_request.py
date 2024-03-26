from dataclasses import dataclass

@dataclass
class Access_Request:
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
