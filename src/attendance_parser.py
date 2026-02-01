"""
Attendance Report Parser
Parses Excel attendance reports from Contineo OBE software to extract lecture dates.
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple


def parse_attendance_file(file_content: bytes, year: int = None) -> Dict:
    """
    Parse attendance file content to extract lecture dates.
    
    The Contineo attendance format has:
    - Month headers in a row: Jun, Jul, Aug, Sep, Oct, Nov, Dec, etc.
    - Day numbers in the row below each month header
    - Attendance marks (P/A/numeric) in subsequent rows
    
    Args:
        file_content: Raw bytes of the uploaded file
        year: Year for the dates (defaults to current year)
    
    Returns:
        Dict with extracted dates and metadata
    """
    if year is None:
        year = datetime.now().year
    
    # Try to decode the content
    try:
        text = file_content.decode('utf-16-le', errors='ignore')
    except:
        try:
            text = file_content.decode('latin-1', errors='ignore')
        except:
            text = file_content.decode('utf-8', errors='ignore')
    
    # Clean up the text
    text = ''.join(c if c.isprintable() or c in '\n\t\r' else ' ' for c in text)
    
    # Month name to number mapping
    month_map = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }
    
    dates = set()
    
    # Strategy 1: Look for month-day patterns in sequence
    # Pattern: Month followed by day numbers
    month_pattern = r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b'
    
    matches = list(re.finditer(month_pattern, text, re.IGNORECASE))
    
    for i, match in enumerate(matches):
        month_name = match.group(1).lower()[:3]
        month_num = month_map.get(month_name)
        if not month_num:
            continue
        
        # Look for day numbers after the month
        start_pos = match.end()
        # Get text until next month or end
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = min(start_pos + 500, len(text))
        
        segment = text[start_pos:end_pos]
        
        # Extract day numbers (1-31)
        day_nums = re.findall(r'\b([1-9]|[12]\d|3[01])\b', segment)
        
        for day_str in day_nums[:32]:  # Max 31 days per month
            try:
                day = int(day_str)
                if 1 <= day <= 31:
                    # Determine year (if month is Jul-Dec, use first year; Jan-Jun use second year for odd semesters)
                    date_year = year
                    try:
                        date_obj = datetime(date_year, month_num, day)
                        dates.add(date_obj.strftime('%Y-%m-%d'))
                    except ValueError:
                        pass  # Invalid date
            except ValueError:
                pass
    
    # Strategy 2: Look for date strings directly
    # DD/MM/YYYY or DD-MM-YYYY
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
    ]
    
    for pattern in date_patterns:
        for match in re.finditer(pattern, text):
            groups = match.groups()
            try:
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    year_val, month_val, day_val = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # DD-MM-YYYY
                    day_val, month_val, year_val = int(groups[0]), int(groups[1]), int(groups[2])
                
                if 2020 <= year_val <= 2030 and 1 <= month_val <= 12 and 1 <= day_val <= 31:
                    date_obj = datetime(year_val, month_val, day_val)
                    dates.add(date_obj.strftime('%Y-%m-%d'))
            except ValueError:
                pass
    
    # Strategy 3: Parse the "From Date:DD-MM-YYYY To DD-MM-YYYY" pattern
    date_range_pattern = r'From\s*Date\s*:\s*(\d{1,2})-(\d{1,2})-(\d{4})\s*To\s*(\d{1,2})-(\d{1,2})-(\d{4})'
    range_match = re.search(date_range_pattern, text, re.IGNORECASE)
    
    metadata = {}
    if range_match:
        try:
            d1, m1, y1, d2, m2, y2 = [int(x) for x in range_match.groups()]
            metadata['from_date'] = f"{y1}-{m1:02d}-{d1:02d}"
            metadata['to_date'] = f"{y2}-{m2:02d}-{d2:02d}"
        except ValueError:
            pass
    
    # Extract course info
    course_match = re.search(r'COURSE\s*:\s*([^\(]+)\((\w+)\)', text, re.IGNORECASE)
    if course_match:
        metadata['course_name'] = course_match.group(1).strip()
        metadata['course_code'] = course_match.group(2).strip()
    
    # Sort dates
    sorted_dates = sorted(list(dates))
    
    return {
        'dates': sorted_dates,
        'count': len(sorted_dates),
        'metadata': metadata
    }


def parse_csv_attendance(content: str, year: int = None) -> Dict:
    """
    Parse CSV attendance data to extract lecture dates.
    
    Args:
        content: CSV text content
        year: Year for the dates
    
    Returns:
        Dict with extracted dates
    """
    if year is None:
        year = datetime.now().year
    
    dates = set()
    
    # Look for date patterns
    # DD/MM/YYYY
    for match in re.finditer(r'(\d{1,2})/(\d{1,2})/(\d{4})', content):
        try:
            d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if 1 <= d <= 31 and 1 <= m <= 12:
                dates.add(f"{y}-{m:02d}-{d:02d}")
        except ValueError:
            pass
    
    # YYYY-MM-DD
    for match in re.finditer(r'(\d{4})-(\d{1,2})-(\d{1,2})', content):
        try:
            y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if 1 <= d <= 31 and 1 <= m <= 12:
                dates.add(f"{y}-{m:02d}-{d:02d}")
        except ValueError:
            pass
    
    return {
        'dates': sorted(list(dates)),
        'count': len(dates)
    }
