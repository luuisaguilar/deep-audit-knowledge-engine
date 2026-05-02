import re

def sanitize_filename(filename: str) -> str:
    """
    Removes or replaces characters that are illegal in Windows filenames.
    """
    # Replace illegal characters with underscore
    # Illegal: < > : " / \ | ? *
    return re.sub(r'[<>:"/\\|?*]', '_', filename)
