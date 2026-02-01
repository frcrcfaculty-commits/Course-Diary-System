"""
Syllabus Parser
Parses PDF syllabus documents to extract course outcomes based on course code.
"""

import re
from typing import List, Dict, Optional
import os


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        filepath: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    try:
        from pdfminer.high_level import extract_text
        return extract_text(filepath)
    except ImportError:
        # Fallback: try PyPDF2
        try:
            import PyPDF2
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise ImportError("Please install pdfminer.six or PyPDF2: pip install pdfminer.six")


def find_course_section(text: str, course_code: str) -> Optional[str]:
    """
    Find the section of text that pertains to a specific course code.
    
    Args:
        text: Full syllabus text
        course_code: Course code to search for (e.g., "BSC12CS05", "25ESC11CS02")
        
    Returns:
        Section of text for the course, or None if not found
    """
    # Create variations of the course code for matching
    code_patterns = [
        course_code,
        course_code.replace(' ', ''),
        course_code.upper(),
        course_code.lower(),
        # Handle codes like "25ESC11CS02" -> also match "ESC11CS02"
        re.sub(r'^\d+', '', course_code),
    ]
    
    # Try to find the course code in the text
    for pattern in code_patterns:
        if pattern in text:
            # Find the position
            idx = text.find(pattern)
            
            # Extract a section around and after the course code
            # Usually, course outcomes are within 3000 characters after the code
            start = max(0, idx - 200)
            end = min(len(text), idx + 5000)
            
            section = text[start:end]
            return section
    
    return None


def extract_course_outcomes(text: str) -> List[Dict]:
    """
    Extract course outcomes from text.
    
    Args:
        text: Text containing course outcomes
        
    Returns:
        List of course outcome dictionaries
    """
    outcomes = []
    
    # Simple pattern: CO followed by number, then capture until next CO or line break
    # Pattern: CO1, CO2, etc. followed by description on same line
    co_pattern = r'CO\s*(\d+)\s*[:\.\-]?\s*([^\n]+)'
    
    matches = re.findall(co_pattern, text, re.IGNORECASE)
    
    for match in matches:
        co_num = match[0]
        statement = match[1].strip()
        
        # Clean up the statement
        statement = re.sub(r'\s+', ' ', statement)
        statement = statement.strip()
        
        # Skip if too short or looks like a header/noise
        if len(statement) < 15:
            continue
        
        # Skip if it looks like just numbers or special characters
        if re.match(r'^[\d\s\.\,\-]+$', statement):
            continue
        
        # Determine Bloom's level from keywords
        blooms_level = determine_blooms_level(statement)
        
        # Avoid duplicates - keep the first occurrence with substantial content
        co_id = f"CO{co_num}"
        existing = next((o for o in outcomes if o['co_id'] == co_id), None)
        if existing:
            # Keep the longer statement
            if len(statement) > len(existing['statement']):
                existing['statement'] = statement
                existing['blooms_level'] = blooms_level
        else:
            outcomes.append({
                'co_id': co_id,
                'statement': statement,
                'blooms_level': blooms_level
            })
    
    # Sort by CO number
    outcomes.sort(key=lambda x: int(re.search(r'\d+', x['co_id']).group()))
    
    return outcomes


def determine_blooms_level(statement: str) -> int:
    """
    Determine Bloom's Taxonomy level from a CO statement.
    
    Args:
        statement: CO statement text
        
    Returns:
        Bloom's level (1-6)
    """
    statement_lower = statement.lower()
    
    # Level 6: Create
    create_keywords = ['create', 'design', 'develop', 'construct', 'produce', 'invent', 'compose', 'formulate', 'assemble']
    if any(keyword in statement_lower for keyword in create_keywords):
        return 6
    
    # Level 5: Evaluate
    evaluate_keywords = ['evaluate', 'judge', 'assess', 'critique', 'justify', 'argue', 'defend', 'recommend', 'conclude']
    if any(keyword in statement_lower for keyword in evaluate_keywords):
        return 5
    
    # Level 4: Analyze
    analyze_keywords = ['analyze', 'analyse', 'compare', 'contrast', 'differentiate', 'distinguish', 'examine', 'categorize', 'investigate']
    if any(keyword in statement_lower for keyword in analyze_keywords):
        return 4
    
    # Level 3: Apply
    apply_keywords = ['apply', 'implement', 'use', 'execute', 'demonstrate', 'solve', 'compute', 'calculate', 'perform']
    if any(keyword in statement_lower for keyword in apply_keywords):
        return 3
    
    # Level 2: Understand
    understand_keywords = ['understand', 'explain', 'describe', 'discuss', 'interpret', 'summarize', 'classify', 'illustrate']
    if any(keyword in statement_lower for keyword in understand_keywords):
        return 2
    
    # Level 1: Remember (default)
    remember_keywords = ['define', 'list', 'identify', 'recall', 'state', 'name', 'recognize', 'outline']
    if any(keyword in statement_lower for keyword in remember_keywords):
        return 1
    
    # Default to level 2 if no keywords found
    return 2


def parse_syllabus(filepath: str, course_code: str) -> Dict:
    """
    Parse a syllabus PDF and extract course outcomes for a specific course.
    
    Args:
        filepath: Path to the syllabus PDF
        course_code: Course code to find
        
    Returns:
        Dict with course outcomes and metadata
    """
    # Extract text from PDF
    full_text = extract_text_from_pdf(filepath)
    
    # Find the course section
    course_section = find_course_section(full_text, course_code)
    
    if course_section:
        # Extract outcomes from the course section
        outcomes = extract_course_outcomes(course_section)
    else:
        # Try extracting from full text (might get outcomes from other courses)
        outcomes = extract_course_outcomes(full_text)
    
    # Extract books from the course section or full text
    books = extract_books(course_section or full_text)
    
    # Extract course name if present
    course_name = None
    name_pattern = rf'{course_code}\s*[:\-]?\s*([A-Za-z\s&]+?)(?:\n|$)'
    name_match = re.search(name_pattern, full_text, re.IGNORECASE)
    if name_match:
        course_name = name_match.group(1).strip()
    
    return {
        'course_code': course_code,
        'course_name': course_name,
        'outcomes': outcomes,
        'books': books,
        'found': len(outcomes) > 0,
        'course_found': course_section is not None
    }


def extract_books(text: str) -> List[Dict]:
    """
    Extract recommended books from syllabus text.
    Separates textbooks from reference books and extracts all details.
    
    Args:
        text: Syllabus text content
        
    Returns:
        List of book dictionaries with type ('textbook' or 'reference')
    """
    books = []
    
    # Look for separate Text Books and Reference Books sections
    textbook_section = ""
    reference_section = ""
    
    # Pattern for Text Books section
    textbook_pattern = r'(?:Text\s*Books?|Prescribed\s*Books?|Main\s*Books?)[:\s]*\n([\s\S]*?)(?:\n\s*(?:Reference|Suggested|Additional|Recommended\s*Reference)|$)'
    textbook_match = re.search(textbook_pattern, text, re.IGNORECASE)
    if textbook_match:
        textbook_section = textbook_match.group(1)
    
    # Pattern for Reference Books section
    reference_pattern = r'(?:Reference\s*Books?|Suggested\s*Readings?|Additional\s*Books?|Recommended\s*Reference)[:\s]*\n([\s\S]*?)(?:\n\s*\n|(?:Module|Unit|CO\s*\d)|$)'
    reference_match = re.search(reference_pattern, text, re.IGNORECASE)
    if reference_match:
        reference_section = reference_match.group(1)
    
    # If no separate sections found, look for combined section
    if not textbook_section and not reference_section:
        combined_pattern = r'(?:Recommended\s*Books?|Books?\s*(?:for\s*)?Reference|Bibliography)[:\s]*\n([\s\S]*?)(?:\n\s*\n|\Z|(?:Module|Unit|CO\s*\d))'
        combined_match = re.search(combined_pattern, text, re.IGNORECASE)
        if combined_match:
            # Treat first 2 as textbooks, rest as reference
            textbook_section = combined_match.group(1)
    
    def parse_book_entries(book_text: str, book_type: str) -> List[Dict]:
        """Parse book entries from a section of text"""
        parsed_books = []
        
        # Pattern 1: "1. Author, 'Title', Publisher, Edition, Year" or "1. Author, Title, Publisher"
        # Common formats in Indian syllabi
        pattern1 = r'(?:^|\n)\s*(\d+)[\.\):\s]+([^,\n]+?),\s*["\']?([^"\'\n,]+)["\']?,?\s*([^,\n]*?)(?:,\s*(\d+(?:st|nd|rd|th)?\s*(?:Ed(?:ition)?)?|Edition\s*\d+))?(?:,\s*(\d{4}))?'
        
        for match in re.finditer(pattern1, book_text, re.MULTILINE | re.IGNORECASE):
            book_id = match.group(1).strip()
            author = match.group(2).strip()
            title = match.group(3).strip()
            publisher = match.group(4).strip() if match.group(4) else ''
            edition = match.group(5).strip() if match.group(5) else ''
            year = match.group(6) if match.group(6) else ''
            
            # Clean up publisher - remove year if it got caught
            publisher = re.sub(r'\d{4}', '', publisher).strip()
            publisher = publisher.rstrip(',. ')
            
            # Skip if looks like CO or Module
            if re.match(r'^CO\d|^Module|^Unit|^L\d', author, re.IGNORECASE):
                continue
            
            # Ensure sensible lengths
            if len(title) > 3:
                parsed_books.append({
                    'id': book_id,
                    'title': title,
                    'author': author,
                    'publisher': publisher,
                    'edition': edition or year,
                    'type': book_type
                })
        
        # Pattern 2: "Author Name, Book Title, Publisher Name, Edition" - comma-separated with implicit ordering
        if len(parsed_books) == 0:
            pattern2 = r'(?:^|\n)\s*(\d+)[\.\):\s]+(.+)'
            for match in re.finditer(pattern2, book_text, re.MULTILINE):
                book_id = match.group(1).strip()
                full_line = match.group(2).strip()
                
                # Skip if looks like CO or Module
                if re.match(r'^CO\d|^Module|^Unit|^L\d', full_line, re.IGNORECASE):
                    continue
                
                parts = [p.strip().strip('"\'') for p in full_line.split(',')]
                
                if len(parts) >= 2:
                    # Heuristic: Author usually first, Title has more words or is in quotes
                    author = parts[0]
                    title = parts[1]
                    publisher = parts[2] if len(parts) > 2 else ''
                    edition = parts[3] if len(parts) > 3 else ''
                    
                    # Extract edition if it looks like "2nd Ed" or "Edition 3"
                    edition_match = re.search(r'(\d+(?:st|nd|rd|th)?\s*(?:Ed(?:ition)?)?|Edition\s*\d+)', full_line, re.IGNORECASE)
                    if edition_match:
                        edition = edition_match.group(1)
                    
                    if len(title) > 3:
                        parsed_books.append({
                            'id': book_id,
                            'title': title,
                            'author': author,
                            'publisher': publisher.rstrip(',. '),
                            'edition': edition,
                            'type': book_type
                        })
        
        return parsed_books
    
    # Parse textbooks
    if textbook_section:
        books.extend(parse_book_entries(textbook_section, 'textbook'))
    
    # Parse reference books
    if reference_section:
        books.extend(parse_book_entries(reference_section, 'reference'))
    
    # If we found books in a combined section, mark first 2 as textbook
    if len(books) > 0 and not reference_section:
        for i, book in enumerate(books):
            if i >= 2:
                book['type'] = 'reference'
    
    # Deduplicate by title
    seen_titles = set()
    unique_books = []
    for book in books:
        title_lower = book['title'].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_books.append(book)
    
    # Renumber IDs
    for i, book in enumerate(unique_books):
        book['id'] = str(i + 1)
    
    return unique_books[:10]  # Limit to 10 books


def parse_syllabus_content(content: bytes, filename: str, course_code: str) -> Dict:
    """
    Parse syllabus content (uploaded file) to extract course outcomes and books.
    
    Args:
        content: Raw file content
        filename: Original filename
        course_code: Course code to search for
        
    Returns:
        Dict with extracted outcomes and books
    """
    import tempfile
    import os
    
    # Save to temp file
    suffix = os.path.splitext(filename)[1] or '.pdf'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        if suffix.lower() == '.pdf':
            return parse_syllabus(temp_path, course_code)
        elif suffix.lower() in ['.txt', '.text']:
            text = content.decode('utf-8', errors='ignore')
            course_section = find_course_section(text, course_code) or text
            outcomes = extract_course_outcomes(course_section)
            books = extract_books(course_section)
            return {
                'course_code': course_code,
                'outcomes': outcomes,
                'books': books,
                'found': len(outcomes) > 0,
                'course_found': True
            }
        else:
            # Try as text
            text = content.decode('utf-8', errors='ignore')
            outcomes = extract_course_outcomes(text)
            books = extract_books(text)
            return {
                'course_code': course_code,
                'outcomes': outcomes,
                'books': books,
                'found': len(outcomes) > 0,
                'course_found': False
            }
    finally:
        os.unlink(temp_path)
