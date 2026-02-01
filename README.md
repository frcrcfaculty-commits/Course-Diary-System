# Course Diary Automation System

A web-based system for managing and automating the creation of academic course diaries.

## Features

- 📋 **Course Management**: Create and manage multiple course diaries
- 📅 **Lesson Planning**: Track proposed and actual lecture dates
- 🎯 **Course Outcomes**: Define and map COs to Program Outcomes
- 📊 **CO-PO Mapping**: Visual matrix with Bloom's Taxonomy levels
- 📝 **Assessment Tracking**: ISE1, ISE2, tutorials, and exam management
- 📄 **Document Generation**: Export to Word (.docx) format

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
cd src
python app.py
```

### 3. Open in Browser
Navigate to: http://localhost:5001

## Project Structure

```
course_diary_system/
├── config/
│   ├── global_config.json    # Institution settings
│   └── course_schema.json    # Data structure schema
├── data/
│   └── *.json                # Saved course data files
├── output/
│   └── *.docx                # Generated documents
├── src/
│   ├── app.py                # Flask web application
│   └── document_generator.py # Word document generator
├── static/
│   └── styles.css            # CSS styles
├── templates/
│   ├── index.html            # Dashboard
│   └── course_form.html      # Course editor
└── requirements.txt
```

## Usage

1. **Create a Course**: Click "Create New Course Diary" on the dashboard
2. **Fill Basic Info**: Enter course code, name, semester, faculty details
3. **Add Outcomes**: Define Course Outcomes (COs) with Bloom's levels
4. **Create Lesson Plan**: Add topics with dates and CO mappings
5. **Map CO-PO**: Fill the CO-PO matrix with mapping levels (1-3)
6. **Add Assessments**: Define ISE1, ISE2 activities
7. **Generate Document**: Click "Generate" to create Word file

## Configurable Elements

The system supports configuration of:
- Institution details (name, department, HOD)
- Time slots and days
- Bloom's Taxonomy levels
- Program Outcomes (PO1-PO12)
- Activity types
- Rubric templates
- Assessment weightages

---
*Built for Fr. Conceicao Rodrigues College of Engineering*
