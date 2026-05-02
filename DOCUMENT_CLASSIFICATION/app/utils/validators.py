"""
Input Validators - Email, password, file validation functions
"""
import re


def validate_email(email):
    """
    Validate email format
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validate password strength
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password (str): Password to validate
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    errors = []
    
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    
    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one digit')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')
    
    if errors:
        return False, ' | '.join(errors)
    
    return True, 'Valid password'


def validate_filename(filename):
    """
    Validate and sanitize filename
    
    Args:
        filename (str): Filename to validate
    
    Returns:
        tuple: (is_valid: bool, sanitized_filename: str)
    """
    if not filename:
        return False, ''
    
    # Remove path separators and null bytes
    sanitized = filename.replace('/', '').replace('\\', '').replace('\0', '')
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    if not sanitized:
        return False, ''
    
    # Check length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return True, sanitized


def validate_file_extension(filename, allowed_extensions):
    """
    Validate file extension
    
    Args:
        filename (str): Filename to check
        allowed_extensions (set): Set of allowed extensions (without dot)
    
    Returns:
        bool: True if extension is allowed
    """
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions


def validate_tags(tags):
    """
    Validate and clean tags
    
    Args:
        tags (list or str): Tags to validate
    
    Returns:
        tuple: (is_valid: bool, clean_tags: list)
    """
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(',')]
    
    if not isinstance(tags, list):
        return False, []
    
    # Remove empty tags, limit to 20 tags, max 50 chars each
    clean_tags = [
        tag.strip()[:50]
        for tag in tags
        if tag.strip()
    ][:20]
    
    if not clean_tags:
        return False, []
    
    return True, clean_tags


def sanitize_input(user_input):
    """
    Sanitize user input to prevent XSS attacks
    
    Args:
        user_input (str): User input to sanitize
    
    Returns:
        str: Sanitized input
    """
    if not user_input:
        return ''
    
    # Remove HTML tags
    sanitized = re.sub(r'<[^>]*>', '', str(user_input))
    
    # Remove special characters that could cause issues
    sanitized = sanitized.replace(';', '').replace('--', '')
    
    return sanitized.strip()
