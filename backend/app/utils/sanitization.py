import re

def sanitize_query(query: str) -> str:
    """
    Sanitize the user's natural language query.
    Removes null bytes and control characters while preserving legitimate technical content.
    """
    if not query:
        return ""
    # Remove null bytes
    query = query.replace("\x00", "")
    # Remove other potentially dangerous control characters but keep newlines/tabs
    query = re.sub(r'[\x01-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', query)
    
    # Optional length check
    if len(query) > 2000:
        query = query[:2000]
        
    return query.strip()
