"""
Timetable Parser Module
Extracts course schedule information from uploaded timetables
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json


# Standard time slots used in most colleges
STANDARD_TIME_SLOTS = [
    ("08:45", "09:45"),
    ("09:45", "10:45"),
    ("10:45", "11:00"),  # Break
    ("11:00", "12:00"),
    ("12:00", "13:00"),
    ("13:00", "13:30"),  # Lunch
    ("13:30", "14:30"),
    ("14:30", "15:30"),
    ("15:30", "16:30"),
]

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAY_ABBREVIATIONS = {
    "mon": "Monday", "monday": "Monday", "m": "Monday",
    "tue": "Tuesday", "tuesday": "Tuesday", "tu": "Tuesday",
    "wed": "Wednesday", "wednesday": "Wednesday", "w": "Wednesday",
    "thu": "Thursday", "thursday": "Thursday", "th": "Thursday",
    "fri": "Friday", "friday": "Friday", "f": "Friday",
    "sat": "Saturday", "saturday": "Saturday", "s": "Saturday",
}


class TimetableParser:
    """Parse timetable data to extract course schedule"""
    
    def __init__(self):
        self.time_slots = STANDARD_TIME_SLOTS
        self.days = DAYS_OF_WEEK
    
    def parse_text_timetable(self, text: str) -> Dict:
        """
        Parse a text-based timetable
        
        Expected formats:
        - Table format: Day | Time1 | Time2 | ...
        - List format: Monday: 9:00-10:00 CourseA, 11:00-12:00 CourseB
        
        Returns:
            Dictionary with parsed schedule
        """
        lines = text.strip().split('\n')
        schedule = {day: [] for day in self.days}
        
        # Try to detect format
        if '|' in text:
            return self._parse_table_format(lines)
        elif ':' in text and any(day.lower() in text.lower() for day in self.days):
            return self._parse_list_format(lines)
        else:
            return self._parse_simple_format(lines)
    
    def _parse_table_format(self, lines: List[str]) -> Dict:
        """Parse pipe-delimited table format"""
        schedule = {day: [] for day in self.days}
        
        # Find header row with time slots
        header_idx = -1
        time_columns = []
        
        for i, line in enumerate(lines):
            if '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                # Check if this looks like a header (contains time-like patterns)
                time_pattern = re.compile(r'\d{1,2}[:.]\d{2}|\d{1,2}\s*(am|pm|AM|PM)')
                times_found = [p for p in parts if time_pattern.search(p)]
                if len(times_found) >= 3:
                    header_idx = i
                    time_columns = parts[1:]  # Skip first column (Day)
                    break
        
        if header_idx == -1:
            return schedule
        
        # Parse data rows
        for line in lines[header_idx + 1:]:
            if '|' not in line:
                continue
            
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if not parts:
                continue
            
            # First column is day
            day_text = parts[0].lower()
            day = None
            for abbr, full_day in DAY_ABBREVIATIONS.items():
                if abbr in day_text:
                    day = full_day
                    break
            
            if not day:
                continue
            
            # Remaining columns are course entries
            for i, entry in enumerate(parts[1:]):
                if entry and entry != '-' and entry.lower() not in ['break', 'lunch', 'recess']:
                    time_slot = time_columns[i] if i < len(time_columns) else f"Slot {i+1}"
                    schedule[day].append({
                        "time": time_slot,
                        "course": entry,
                        "slot_index": i
                    })
        
        return schedule
    
    def _parse_list_format(self, lines: List[str]) -> Dict:
        """Parse list format: Monday: 9:00-10:00 CourseA"""
        schedule = {day: [] for day in self.days}
        current_day = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with a day
            for abbr, full_day in DAY_ABBREVIATIONS.items():
                if line.lower().startswith(abbr):
                    current_day = full_day
                    # Extract rest of line after colon
                    if ':' in line:
                        line = line.split(':', 1)[1].strip()
                    break
            
            if current_day and line:
                # Parse time and course
                time_pattern = re.compile(r'(\d{1,2}[:.]\d{2})\s*[-–]\s*(\d{1,2}[:.]\d{2})\s*(.+)')
                match = time_pattern.search(line)
                if match:
                    start_time, end_time, course = match.groups()
                    schedule[current_day].append({
                        "time": f"{start_time}-{end_time}",
                        "start": start_time,
                        "end": end_time,
                        "course": course.strip()
                    })
        
        return schedule
    
    def _parse_simple_format(self, lines: List[str]) -> Dict:
        """Parse simple format - just course names in grid"""
        schedule = {day: [] for day in self.days}
        
        for i, line in enumerate(lines):
            parts = line.strip().split()
            if parts:
                # Assume first word might be a day
                first = parts[0].lower().rstrip(':,')
                if first in DAY_ABBREVIATIONS:
                    day = DAY_ABBREVIATIONS[first]
                    for j, course in enumerate(parts[1:]):
                        if course and course != '-':
                            schedule[day].append({
                                "time": self.time_slots[j] if j < len(self.time_slots) else f"Slot {j+1}",
                                "course": course,
                                "slot_index": j
                            })
        
        return schedule
    
    def extract_course_schedule(self, schedule: Dict, course_code: str) -> Dict:
        """
        Extract specific course schedule from full timetable
        
        Args:
            schedule: Full parsed schedule
            course_code: Course code to search for
            
        Returns:
            Course-specific schedule with days and hours
        """
        course_schedule = {
            "course_code": course_code,
            "teaching_days": [],
            "slots": [],
            "total_hours_per_week": 0
        }
        
        code_lower = course_code.lower()
        
        for day, slots in schedule.items():
            day_slots = []
            for slot in slots:
                course_name = slot.get("course", "").lower()
                # Match if course code appears in the slot
                if code_lower in course_name or self._fuzzy_match(course_code, slot.get("course", "")):
                    day_slots.append(slot)
            
            if day_slots:
                course_schedule["teaching_days"].append(day)
                for slot in day_slots:
                    course_schedule["slots"].append({
                        "day": day,
                        "time": slot.get("time"),
                        "slot_index": slot.get("slot_index", 0)
                    })
                    course_schedule["total_hours_per_week"] += 1
        
        return course_schedule
    
    def _fuzzy_match(self, code: str, text: str) -> bool:
        """Fuzzy match course code in text"""
        if not text:
            return False
        
        # Remove common delimiters and compare
        code_clean = re.sub(r'[^a-zA-Z0-9]', '', code.lower())
        text_clean = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
        
        return code_clean in text_clean
    
    def generate_lesson_dates(self, course_schedule: Dict, 
                             start_date: str, 
                             end_date: str,
                             holidays: List[str] = None) -> List[Dict]:
        """
        Generate lesson plan dates based on course schedule
        
        Args:
            course_schedule: Course schedule from extract_course_schedule
            start_date: Semester start date (YYYY-MM-DD)
            end_date: Semester end date (YYYY-MM-DD)
            holidays: List of holiday dates to skip
            
        Returns:
            List of proposed lesson dates
        """
        if holidays is None:
            holidays = []
        
        holiday_set = set(holidays)
        teaching_days = course_schedule.get("teaching_days", [])
        
        if not teaching_days:
            return []
        
        # Map day names to weekday numbers
        day_to_num = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        
        teaching_weekdays = [day_to_num[d] for d in teaching_days]
        
        # Parse dates
        try:
            current = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return []
        
        lesson_dates = []
        lesson_number = 1
        
        while current <= end:
            if current.weekday() in teaching_weekdays:
                date_str = current.strftime("%Y-%m-%d")
                if date_str not in holiday_set:
                    # Find which slot this is
                    day_name = teaching_days[teaching_weekdays.index(current.weekday())]
                    matching_slots = [s for s in course_schedule.get("slots", []) 
                                     if s.get("day") == day_name]
                    
                    for slot in matching_slots:
                        lesson_dates.append({
                            "sr_no": lesson_number,
                            "proposed_date": date_str,
                            "day": day_name,
                            "time": slot.get("time", ""),
                            "actual_date": "",
                            "topic": "",
                            "delivery_mode": "Lecture",
                            "co_mapping": [],
                            "assessment_tool": [],
                            "reference_book": ""
                        })
                        lesson_number += 1
            
            current += timedelta(days=1)
        
        return lesson_dates
    
    def get_summary(self, course_schedule: Dict) -> str:
        """Generate human-readable summary of course schedule"""
        days = course_schedule.get("teaching_days", [])
        hours = course_schedule.get("total_hours_per_week", 0)
        
        if not days:
            return "No schedule found for this course"
        
        day_str = ", ".join(days)
        return f"This course is taught on {day_str} ({hours} hour{'s' if hours != 1 else ''}/week)"


def parse_timetable_text(text: str) -> Dict:
    """Convenience function to parse timetable text"""
    parser = TimetableParser()
    return parser.parse_text_timetable(text)


def get_course_schedule(timetable: Dict, course_code: str) -> Dict:
    """Convenience function to extract course schedule"""
    parser = TimetableParser()
    return parser.extract_course_schedule(timetable, course_code)


def generate_dates(course_schedule: Dict, start_date: str, end_date: str, holidays: List[str] = None) -> List[Dict]:
    """Convenience function to generate lesson dates"""
    parser = TimetableParser()
    return parser.generate_lesson_dates(course_schedule, start_date, end_date, holidays)
