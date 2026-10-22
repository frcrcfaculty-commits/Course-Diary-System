"""
Course Diary Automation System - Flask Web Application
Provides web interface for managing course diaries
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = 'course_diary_secret_key_2026'

# Paths
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_PATH, 'config')
DATA_PATH = os.path.join(BASE_PATH, 'data')
OUTPUT_PATH = os.path.join(BASE_PATH, 'output')

# On Vercel the code directory is read-only: work on a /tmp copy of the
# bundled course data, refreshed from the repo on each cold start.
if os.environ.get('VERCEL'):
    import shutil
    _bundled = DATA_PATH
    DATA_PATH = '/tmp/course_diary/data'
    OUTPUT_PATH = '/tmp/course_diary/output'
    if not os.path.isdir(DATA_PATH):
        shutil.copytree(_bundled, DATA_PATH, copy_function=shutil.copyfile)

# Ensure directories exist
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)


def load_global_config():
    """Load global configuration"""
    with open(os.path.join(CONFIG_PATH, 'global_config.json'), 'r') as f:
        return json.load(f)


def get_courses():
    """Get list of all saved courses"""
    courses = []
    if os.path.exists(DATA_PATH):
        for filename in os.listdir(DATA_PATH):
            if filename.endswith('.json'):
                filepath = os.path.join(DATA_PATH, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    courses.append({
                        'filename': filename,
                        'course_code': data['course_info']['course_code'],
                        'course_name': data['course_info']['course_name'],
                        'semester': data['course_info']['semester'],
                        'academic_year': data['course_info']['academic_year']
                    })
    return courses


@app.route('/')
def index():
    """Home page - Dashboard"""
    config = load_global_config()
    courses = get_courses()
    return render_template('index.html', 
                         config=config, 
                         courses=courses,
                         institution=config['institution'])


@app.route('/course/new', methods=['GET', 'POST'])
def new_course():
    """Create new course form"""
    config = load_global_config()
    
    if request.method == 'POST':
        # Process form data
        course_data = {
            'course_info': {
                'course_code': request.form.get('course_code'),
                'course_name': request.form.get('course_name'),
                'course_type': request.form.get('course_type'),
                'semester': request.form.get('semester'),
                'academic_year': request.form.get('academic_year'),
                'faculty_name': request.form.get('faculty_name'),
                'faculty_designation': request.form.get('faculty_designation'),
                'branch': request.form.get('branch'),
                'division': request.form.get('division', ''),
                'batches': request.form.get('batches', '').split(',')
            },
            'course_outcomes': [],
            'co_po_mapping': [],
            'lesson_plan': [],
            'assessments': {'ise1': [], 'ise2': [], 'tutorials': []},
            'recommended_books': [],
            'exit_survey': {'questions': [], 'responses': []}
        }
        
        # Save course data
        filename = f"course_{course_data['course_info']['course_code']}_{course_data['course_info']['academic_year'].replace('-', '_')}.json"
        filepath = os.path.join(DATA_PATH, filename)
        
        with open(filepath, 'w') as f:
            json.dump(course_data, f, indent=2)
        
        # Redirect to syllabus upload page to extract COs and books
        return redirect(url_for('syllabus_upload_page', filename=filename))
    
    return render_template('course_form.html', 
                         config=config,
                         course=None,
                         mode='new')


@app.route('/course/<filename>/syllabus-setup')
def syllabus_upload_page(filename):
    """Syllabus upload page for extracting COs and Books"""
    config = load_global_config()
    
    filepath = os.path.join(DATA_PATH, filename)
    if not os.path.exists(filepath):
        return "Course not found", 404
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    return render_template('syllabus_setup.html',
                         config=config,
                         course=course,
                         filename=filename)


@app.route('/course/edit/<filename>')
def edit_course(filename):
    """Edit existing course"""
    config = load_global_config()
    
    filepath = os.path.join(DATA_PATH, filename)
    if not os.path.exists(filepath):
        return "Course not found", 404
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    return render_template('course_form.html',
                         config=config,
                         course=course,
                         filename=filename,
                         mode='edit')


@app.route('/api/course/<filename>', methods=['GET', 'PUT', 'DELETE'])
def api_course(filename):
    """API to get/update/delete course data"""
    filepath = os.path.join(DATA_PATH, filename)
    
    if request.method == 'GET':
        if not os.path.exists(filepath):
            return jsonify({'error': 'Course not found'}), 404
        with open(filepath, 'r') as f:
            return jsonify(json.load(f))
    
    elif request.method == 'PUT':
        data = request.json
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return jsonify({'success': True, 'message': 'Course saved successfully'})
    
    elif request.method == 'DELETE':
        if not os.path.exists(filepath):
            return jsonify({'error': 'Course not found'}), 404
        os.remove(filepath)
        return jsonify({'success': True, 'message': 'Course deleted successfully'})


@app.route('/api/course/<filename>/basic_info', methods=['POST'])
def save_basic_info(filename):
    """Save basic course info"""
    filepath = os.path.join(DATA_PATH, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'Course not found'}), 404
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    data = request.json
    course['course_info'] = {
        'course_code': data.get('course_code', ''),
        'course_name': data.get('course_name', ''),
        'course_type': data.get('course_type', 'theory'),
        'semester': data.get('semester', ''),
        'academic_year': data.get('academic_year', ''),
        'faculty_name': data.get('faculty_name', ''),
        'faculty_designation': data.get('faculty_designation', ''),
        'branch': data.get('branch', ''),
        'division': data.get('division', ''),
        'batches': data.get('batches', [])
    }
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True, 'message': 'Basic info saved successfully'})


@app.route('/api/course/<filename>/outcomes', methods=['POST'])
def save_outcomes(filename):
    """Save course outcomes"""
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    course['course_outcomes'] = request.json.get('outcomes', [])
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True})


@app.route('/api/course/<filename>/lesson_plan', methods=['POST'])
def save_lesson_plan(filename):
    """Save lesson plan"""
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    course['lesson_plan'] = request.json.get('lesson_plan', [])
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True})


@app.route('/api/course/<filename>/co_po_mapping', methods=['POST'])
def save_co_po_mapping(filename):
    """Save CO-PO mapping"""
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    course['co_po_mapping'] = request.json.get('mapping', [])
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True})


@app.route('/api/course/<filename>/assessments', methods=['POST'])
def save_assessments(filename):
    """Save assessments"""
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    course['assessments'] = request.json.get('assessments', {})
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True})


@app.route('/api/course/<filename>/books', methods=['POST'])
def save_books(filename):
    """Save recommended books from form"""
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    course['recommended_books'] = request.json.get('books', [])
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True, 'message': 'Books saved successfully'})


@app.route('/course/<filename>/generate', methods=['POST'])
def generate_document(filename):
    """Generate Word document from course data"""
    from document_generator import CourseDiaryGenerator
    
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    # Generate document
    config_path = os.path.join(CONFIG_PATH, 'global_config.json')
    generator = CourseDiaryGenerator(config_path)
    
    output_filename = f"Course_Diary_{course['course_info']['course_code']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    output_path = os.path.join(OUTPUT_PATH, output_filename)
    
    generator.create_document(course, output_path)
    
    return jsonify({
        'success': True,
        'filename': output_filename,
        'download_url': url_for('download_document', filename=output_filename)
    })


@app.route('/download/<filename>')
def download_document(filename):
    """Download generated document"""
    filepath = os.path.join(OUTPUT_PATH, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found", 404


@app.route('/api/config')
def get_config():
    """Get global configuration"""
    return jsonify(load_global_config())


# ============ AI-Assisted CO-PO Mapping API ============

@app.route('/course/<filename>/ai-mapping')
def ai_mapping_page(filename):
    """AI-assisted CO-PO mapping page"""
    config = load_global_config()
    
    filepath = os.path.join(DATA_PATH, filename)
    if not os.path.exists(filepath):
        return "Course not found", 404
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    return render_template('ai_mapping.html',
                         config=config,
                         course=course,
                         filename=filename)


@app.route('/api/ai/suggest-mapping', methods=['POST'])
def suggest_mapping():
    """Get AI suggestions for a single CO"""
    from co_po_engine import suggest_co_po_mapping
    
    data = request.json
    co_statement = data.get('statement', '')
    bloom_level = data.get('blooms_level')
    course_type = data.get('course_type', 'theory')
    
    suggestions = suggest_co_po_mapping(co_statement, bloom_level, course_type)
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })


@app.route('/api/ai/suggest-all-mappings', methods=['POST'])
def suggest_all_mappings():
    """Get AI suggestions for all COs in a course"""
    from co_po_engine import generate_full_matrix, COPOMappingEngine
    
    data = request.json
    course_outcomes = data.get('course_outcomes', [])
    course_type = data.get('course_type', 'theory')
    
    matrix = generate_full_matrix(course_outcomes, course_type)
    
    # Get PO definitions
    engine = COPOMappingEngine(course_type)
    po_definitions = engine.get_po_definitions()
    
    return jsonify({
        'success': True,
        'matrix': matrix,
        'po_definitions': po_definitions
    })


@app.route('/api/course/<filename>/ai-mapping', methods=['POST'])
def save_ai_mapping(filename):
    """Save AI-assisted CO-PO mappings with justifications"""
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    mapping_data = request.json.get('mappings', [])
    
    # Format mapping data for storage
    formatted_mappings = []
    for co_mapping in mapping_data:
        po_mappings = {}
        for po, details in co_mapping.get('po_mappings', {}).items():
            if details.get('weight', 0) > 0:
                po_mappings[po] = details['weight']
        
        formatted_mappings.append({
            'co_id': co_mapping.get('co_id'),
            'blooms_level': co_mapping.get('blooms_level'),
            'performance_indicator': co_mapping.get('performance_indicator', ''),
            'po_mappings': po_mappings,
            'justification': co_mapping.get('justification', ''),
            'ai_suggested': co_mapping.get('ai_suggested', False),
            'faculty_modified': co_mapping.get('faculty_modified', False)
        })
    
    course['co_po_mapping'] = formatted_mappings
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True, 'message': 'AI-assisted mappings saved'})


@app.route('/api/course/<filename>/attainment', methods=['GET', 'POST'])
def course_attainment(filename):
    """Get or calculate CO/PO attainment"""
    from co_po_engine import COPOMappingEngine
    
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    if request.method == 'POST':
        # Save assessment data and calculate attainment
        assessment_data = request.json.get('assessment_data', {})
        
        engine = COPOMappingEngine(course['course_info'].get('course_type', 'theory'))
        
        # Calculate CO attainment
        co_attainment = engine.calculate_co_attainment(assessment_data)
        
        # Build CO-PO mapping dict
        co_po_mapping = {}
        for mapping in course.get('co_po_mapping', []):
            co_id = mapping['co_id']
            co_po_mapping[co_id] = {}
            for po, weight in mapping.get('po_mappings', {}).items():
                co_po_mapping[co_id][po] = {'weight': weight}
        
        # Calculate PO attainment
        po_attainment = engine.calculate_po_attainment(co_attainment, co_po_mapping)
        
        # Save attainment data
        course['attainment'] = {
            'co_attainment': co_attainment,
            'po_attainment': po_attainment,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(course, f, indent=2)
        
        return jsonify({
            'success': True,
            'co_attainment': co_attainment,
            'po_attainment': po_attainment
        })
    
        # GET - return existing attainment data
        return jsonify({
            'success': True,
            'attainment': course.get('attainment', {})
        })


# ============ Timetable Upload API ============

@app.route('/course/<filename>/timetable')
def timetable_page(filename):
    """Timetable upload and schedule page"""
    config = load_global_config()
    
    filepath = os.path.join(DATA_PATH, filename)
    if not os.path.exists(filepath):
        return "Course not found", 404
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    return render_template('timetable.html',
                         config=config,
                         course=course,
                         filename=filename)


@app.route('/api/course/<filename>/parse-timetable', methods=['POST'])
def parse_timetable(filename):
    """Parse uploaded timetable text and extract schedule"""
    from timetable_parser import TimetableParser
    
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    data = request.json
    timetable_text = data.get('timetable_text', '')
    
    parser = TimetableParser()
    
    # Parse full timetable
    full_schedule = parser.parse_text_timetable(timetable_text)
    
    # Extract schedule for this course
    course_code = course['course_info']['course_code']
    course_schedule = parser.extract_course_schedule(full_schedule, course_code)
    
    # Get summary
    summary = parser.get_summary(course_schedule)
    
    return jsonify({
        'success': True,
        'full_schedule': full_schedule,
        'course_schedule': course_schedule,
        'summary': summary
    })


@app.route('/api/course/<filename>/upload-timetable', methods=['POST'])
def upload_timetable_file(filename):
    """Upload and parse timetable from CSV or image file"""
    import csv
    import io
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'No file selected'})
    
    filename_lower = file.filename.lower()
    extracted_text = ''
    
    try:
        if filename_lower.endswith('.csv'):
            # Handle CSV file
            content = file.read().decode('utf-8')
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            
            # Convert CSV to pipe-separated format
            lines = []
            for row in rows:
                lines.append(' | '.join(cell.strip() for cell in row))
            extracted_text = '\n'.join(lines)
            
        elif filename_lower.endswith(('.png', '.jpg', '.jpeg')):
            # Handle image file - try OCR
            try:
                import pytesseract
                from PIL import Image
                
                image = Image.open(file)
                extracted_text = pytesseract.image_to_string(image)
            except ImportError:
                # pytesseract not installed - provide instructions
                return jsonify({
                    'success': False,
                    'error': 'Image OCR requires pytesseract. Please install: pip install pytesseract pillow, and install Tesseract OCR on your system.'
                })
            except Exception as ocr_e:
                return jsonify({
                    'success': False,
                    'error': f'OCR failed: {str(ocr_e)}. Try pasting the timetable as text instead.'
                })
        else:
            return jsonify({'success': False, 'error': 'Unsupported file type. Use CSV or PNG/JPG'})
        
        return jsonify({
            'success': True,
            'extracted_text': extracted_text
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/course/<filename>/save-timetable', methods=['POST'])
def save_timetable(filename):
    """Save timetable data to course"""
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    data = request.json
    
    course['timetable'] = {
        'raw_text': data.get('raw_text', ''),
        'full_schedule': data.get('full_schedule', {}),
        'course_schedule': data.get('course_schedule', {}),
        'summary': data.get('summary', ''),
        'last_updated': datetime.now().isoformat()
    }
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True, 'message': 'Timetable saved'})


@app.route('/api/course/<filename>/generate-lesson-dates', methods=['POST'])
def generate_lesson_dates(filename):
    """Generate lesson plan dates based on timetable"""
    from timetable_parser import TimetableParser
    
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    data = request.json
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    holidays = data.get('holidays', [])
    
    # Get course schedule from saved timetable
    course_schedule = course.get('timetable', {}).get('course_schedule', {})
    
    if not course_schedule.get('teaching_days'):
        return jsonify({
            'success': False,
            'error': 'No timetable saved. Please upload timetable first.'
        })
    
    parser = TimetableParser()
    lesson_dates = parser.generate_lesson_dates(course_schedule, start_date, end_date, holidays)
    
    return jsonify({
        'success': True,
        'lesson_dates': lesson_dates,
        'total_lectures': len(lesson_dates)
    })


@app.route('/api/course/<filename>/apply-lesson-dates', methods=['POST'])
def apply_lesson_dates(filename):
    """Apply generated lesson dates to lesson plan"""
    filepath = os.path.join(DATA_PATH, filename)
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    data = request.json
    lesson_dates = data.get('lesson_dates', [])
    
    # Merge with existing lesson plan or replace
    existing_plan = course.get('lesson_plan', [])
    
    if data.get('replace', False) or not existing_plan:
        course['lesson_plan'] = lesson_dates
    else:
        # Update proposed dates for existing entries
        for i, date_entry in enumerate(lesson_dates):
            if i < len(existing_plan):
                existing_plan[i]['proposed_date'] = date_entry['proposed_date']
                existing_plan[i]['day'] = date_entry.get('day', '')
                existing_plan[i]['time'] = date_entry.get('time', '')
        course['lesson_plan'] = existing_plan
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True, 'message': 'Lesson dates applied'})


# ============ Attendance Upload API ============

@app.route('/api/course/<filename>/parse-attendance', methods=['POST'])
def parse_attendance(filename):
    """Parse uploaded attendance file to extract lecture dates"""
    from attendance_parser import parse_attendance_file, parse_csv_attendance
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    try:
        content = file.read()
        
        # Get year from form data or use current year
        year = request.form.get('year', datetime.now().year)
        if isinstance(year, str):
            year = int(year)
        
        # Parse based on file type
        if file.filename.endswith('.csv') or file.filename.endswith('.txt'):
            text_content = content.decode('utf-8', errors='ignore')
            result = parse_csv_attendance(text_content, year)
        else:
            result = parse_attendance_file(content, year)
        
        return jsonify({
            'success': True,
            'dates': result.get('dates', []),
            'count': result.get('count', 0),
            'metadata': result.get('metadata', {})
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ Syllabus Upload API ============

@app.route('/api/course/<filename>/parse-syllabus', methods=['POST'])
def parse_syllabus_upload(filename):
    """Parse uploaded syllabus to extract course outcomes"""
    from syllabus_parser import parse_syllabus_content
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Get the course code from the course file
    filepath = os.path.join(DATA_PATH, filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'Course not found'}), 404
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    course_code = course.get('course_info', {}).get('course_code', '')
    if not course_code:
        return jsonify({'success': False, 'error': 'No course code found in Basic Info'}), 400
    
    try:
        content = file.read()
        result = parse_syllabus_content(content, file.filename, course_code)
        
        return jsonify({
            'success': True,
            'course_code': course_code,
            'outcomes': result.get('outcomes', []),
            'books': result.get('books', []),
            'count': len(result.get('outcomes', [])),
            'books_count': len(result.get('books', [])),
            'course_found': result.get('course_found', False)
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500


@app.route('/api/course/<filename>/apply-outcomes', methods=['POST'])
def apply_outcomes(filename):
    """Apply parsed course outcomes to the course file"""
    filepath = os.path.join(DATA_PATH, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'Course not found'}), 404
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    data = request.json
    outcomes = data.get('outcomes', [])
    replace = data.get('replace', False)
    
    if replace or not course.get('course_outcomes'):
        course['course_outcomes'] = outcomes
    else:
        # Merge: add new outcomes that don't exist
        existing_ids = {co['co_id'] for co in course.get('course_outcomes', [])}
        for outcome in outcomes:
            if outcome['co_id'] not in existing_ids:
                course['course_outcomes'].append(outcome)
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True, 'message': f'Applied {len(outcomes)} course outcomes'})


@app.route('/api/course/<filename>/apply-books', methods=['POST'])
def apply_books(filename):
    """Apply parsed books to the course file"""
    filepath = os.path.join(DATA_PATH, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'Course not found'}), 404
    
    with open(filepath, 'r') as f:
        course = json.load(f)
    
    data = request.json
    books = data.get('books', [])
    replace = data.get('replace', False)
    
    if replace or not course.get('recommended_books'):
        course['recommended_books'] = books
    else:
        # Merge: add new books
        existing_titles = {b.get('title', '').lower() for b in course.get('recommended_books', [])}
        for book in books:
            if book.get('title', '').lower() not in existing_titles:
                course['recommended_books'].append(book)
    
    with open(filepath, 'w') as f:
        json.dump(course, f, indent=2)
    
    return jsonify({'success': True, 'message': f'Applied {len(books)} books'})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
