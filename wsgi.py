"""
WSGI entry point for PythonAnywhere deployment
"""

import sys
import os

# Add the project path to Python path
project_path = '/home/YOUR_USERNAME/course_diary_system'  # Update with your PythonAnywhere username
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Add the src directory
src_path = os.path.join(project_path, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import the Flask app
from app import app as application

# This is needed for PythonAnywhere
