import os

def is_configured(secret_name: str) -> bool:
    """
    Check if a required configuration/secret is present in the environment without printing it.
    """
    value = os.getenv(secret_name)
    if value and value.strip() != "":
        return True
    return False
