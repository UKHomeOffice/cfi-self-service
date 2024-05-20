
from dataclasses import dataclass

@dataclass
class Environment_URLs:
 
    test_environment_url: str = ""
    dev_environment_url: str = ""
    prod_environment_url: str = ""
