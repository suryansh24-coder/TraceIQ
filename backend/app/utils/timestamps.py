from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

def parse_iso_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp to a UTC datetime object."""
    if not ts_str:
        return None
    try:
        # Handle 'Z' suffix for UTC
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None

def sort_events_chronologically(events: List[Dict[str, Any]], key: str = "timestamp") -> List[Dict[str, Any]]:
    """Sort a list of dictionaries containing a timestamp chronologically."""
    def get_sort_key(event: Dict[str, Any]) -> datetime:
        ts = event.get(key)
        if isinstance(ts, str):
            parsed = parse_iso_timestamp(ts)
            return parsed if parsed else datetime.min.replace(tzinfo=timezone.utc)
        elif isinstance(ts, datetime):
            return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        return datetime.min.replace(tzinfo=timezone.utc)
        
    return sorted(events, key=get_sort_key)
