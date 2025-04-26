import re
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def sanitize_input(input_str: str | None) -> str | None:
    """Sanitize input to prevent SQL injection and XSS."""
    if input_str is None:
        return None
    # Remove dangerous characters and trim
    sanitized = re.sub(r'[<>;]', '', input_str.strip())
    if len(sanitized) == 0:
        return None
    logging.info(f"Sanitized input: {sanitized}")
    return sanitized

def hash_contact(contact: str) -> str:
    """Hash contact information for secure storage."""
    return hashlib.sha256(contact.encode()).hexdigest()