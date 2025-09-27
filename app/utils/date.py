import re
from dateutil import parser

DATE_REGEX = re.compile(
    r'(\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*,?\s\d{4}'  
    r'|\d{1,2}-\d{2}-\d{4}'                                                         
    r'|\d{1,2}\s\w+\s\d{4})'                                                        
)


def extract_published_date(raw_content: str):
    """
    Extracts the published date if it's explicitly labeled.
    Otherwise returns None.
    """
    if not raw_content:
        return None

    # Look for "Published" or "Published on ..."
    match = re.search(
        r'(?:Published|Published on|This post was published on)\s*[:\-]?\s*([0-9]{1,2}[-\s/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d+)[a-z]*[-\s,]*\d{4})',
        raw_content,
        re.IGNORECASE
    )
    if match:
        date_str = match.group(1).strip()
        try:
            dt = parser.parse(date_str, dayfirst=True, fuzzy=True)
            return dt.date().isoformat()   # normalize the date format to YYYY-MM-DD
        except Exception:
            return None
    

    return None