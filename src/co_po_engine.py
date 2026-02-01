"""
AI-Assisted CO-PO Mapping Engine
Rule-based suggestions based on Bloom's Taxonomy and course characteristics
"""

import re
from typing import Dict, List, Tuple, Optional


# Bloom's Taxonomy Levels
BLOOMS_LEVELS = {
    1: "Remember",
    2: "Understand",
    3: "Apply",
    4: "Analyze",
    5: "Evaluate",
    6: "Create"
}

# Bloom's Taxonomy Keywords for each level
BLOOMS_KEYWORDS = {
    1: ["define", "list", "recall", "identify", "name", "state", "describe", "memorize", "recognize"],
    2: ["explain", "summarize", "interpret", "classify", "compare", "contrast", "discuss", "understand"],
    3: ["apply", "implement", "solve", "use", "demonstrate", "calculate", "execute", "compute", "perform"],
    4: ["analyze", "examine", "differentiate", "distinguish", "investigate", "categorize", "compare", "experiment"],
    5: ["evaluate", "assess", "justify", "critique", "judge", "determine", "recommend", "conclude", "validate"],
    6: ["create", "design", "develop", "construct", "produce", "invent", "formulate", "compose", "build"]
}

# PO Definitions (NBA standard)
PO_DEFINITIONS = {
    "PO1": {"name": "Engineering Knowledge", "description": "Apply knowledge of mathematics, science, engineering fundamentals"},
    "PO2": {"name": "Problem Analysis", "description": "Identify, formulate, analyze complex engineering problems"},
    "PO3": {"name": "Design/Development", "description": "Design solutions for complex problems and system components"},
    "PO4": {"name": "Conduct Investigations", "description": "Investigate complex problems using research-based knowledge"},
    "PO5": {"name": "Modern Tool Usage", "description": "Create, select, apply appropriate modern engineering tools"},
    "PO6": {"name": "Engineer & Society", "description": "Apply reasoning in contextual knowledge for professional practice"},
    "PO7": {"name": "Environment & Sustainability", "description": "Understand impact of solutions in environmental contexts"},
    "PO8": {"name": "Ethics", "description": "Apply ethical principles and professional responsibilities"},
    "PO9": {"name": "Individual & Team Work", "description": "Function effectively as individual and team member"},
    "PO10": {"name": "Communication", "description": "Communicate effectively on complex engineering activities"},
    "PO11": {"name": "Project Management", "description": "Demonstrate management principles and apply to projects"},
    "PO12": {"name": "Life-long Learning", "description": "Recognize need for and engage in independent learning"}
}

# Keywords that suggest specific PO mappings
PO_KEYWORDS = {
    "PO1": ["knowledge", "mathematics", "science", "fundamental", "engineering", "principle", "concept", "theory"],
    "PO2": ["analyze", "problem", "investigate", "formulate", "identify", "diagnose", "examine"],
    "PO3": ["design", "develop", "solution", "system", "component", "build", "create", "implement", "model"],
    "PO4": ["investigate", "research", "experiment", "validate", "test", "hypothesis", "data", "interpret"],
    "PO5": ["tool", "software", "hardware", "technology", "modern", "simulation", "programming", "code", "implement"],
    "PO6": ["society", "social", "context", "professional", "practice", "impact", "health", "safety"],
    "PO7": ["environment", "sustainable", "green", "ecology", "resource", "conservation", "pollution"],
    "PO8": ["ethics", "ethical", "responsibility", "integrity", "professional", "moral", "legal"],
    "PO9": ["team", "collaborate", "group", "individual", "leadership", "member", "coordinate"],
    "PO10": ["communicate", "present", "report", "document", "write", "speak", "explain", "demonstrate"],
    "PO11": ["manage", "project", "plan", "schedule", "resource", "budget", "risk", "finance"],
    "PO12": ["learn", "update", "emerging", "continuous", "self-study", "adapt", "evolve", "independent"]
}


class COPOMappingEngine:
    """AI-assisted CO-PO Mapping Engine with rule-based suggestions"""
    
    def __init__(self, course_type: str = "theory"):
        """
        Initialize the mapping engine
        
        Args:
            course_type: "theory", "lab", "theory_lab", "theory_tutorial"
        """
        self.course_type = course_type
        self.is_lab = course_type in ["lab", "theory_lab"]
        self.is_design = False  # Set based on course characteristics
    
    def detect_bloom_level(self, co_statement: str) -> int:
        """
        Detect Bloom's taxonomy level from CO statement
        
        Args:
            co_statement: The course outcome statement
            
        Returns:
            Bloom's level (1-6)
        """
        statement_lower = co_statement.lower()
        
        # Check from highest to lowest level
        for level in range(6, 0, -1):
            keywords = BLOOMS_KEYWORDS[level]
            for keyword in keywords:
                if keyword in statement_lower:
                    return level
        
        # Default to level 2 (Understand) if no keywords found
        return 2
    
    def get_keyword_matches(self, co_statement: str) -> Dict[str, List[str]]:
        """
        Find which PO keywords appear in the CO statement
        
        Returns:
            Dictionary of PO -> matched keywords
        """
        statement_lower = co_statement.lower()
        matches = {}
        
        for po, keywords in PO_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in statement_lower]
            if matched:
                matches[po] = matched
        
        return matches
    
    def suggest_mapping(self, co_statement: str, bloom_level: Optional[int] = None) -> Dict[str, Dict]:
        """
        Generate AI suggestions for CO-PO mapping
        
        Args:
            co_statement: The course outcome statement
            bloom_level: Optional override for Bloom's level (1-6)
            
        Returns:
            Dictionary with suggested mappings and rationales
        """
        if bloom_level is None:
            bloom_level = self.detect_bloom_level(co_statement)
        
        keyword_matches = self.get_keyword_matches(co_statement)
        suggestions = {}
        
        # Initialize all POs with 0
        for po in PO_DEFINITIONS.keys():
            suggestions[po] = {
                "weight": 0,
                "rationale": "",
                "confidence": "low",
                "auto_suggested": False
            }
        
        # Rule 1: Bloom level >= 3 (Apply) suggests PO1 (Engineering Knowledge)
        if bloom_level >= 3:
            suggestions["PO1"] = {
                "weight": 2,
                "rationale": f"Bloom level {bloom_level} ({BLOOMS_LEVELS[bloom_level]}) indicates application of engineering knowledge",
                "confidence": "high",
                "auto_suggested": True
            }
        elif bloom_level >= 2:
            suggestions["PO1"] = {
                "weight": 1,
                "rationale": f"Bloom level {bloom_level} ({BLOOMS_LEVELS[bloom_level]}) indicates understanding of fundamentals",
                "confidence": "medium",
                "auto_suggested": True
            }
        
        # Rule 2: Bloom level >= 4 (Analyze) suggests PO2 (Problem Analysis)
        if bloom_level >= 4:
            suggestions["PO2"] = {
                "weight": 2,
                "rationale": f"Bloom level {bloom_level} ({BLOOMS_LEVELS[bloom_level]}) indicates analytical problem-solving skills",
                "confidence": "high",
                "auto_suggested": True
            }
        
        # Rule 3: Bloom level >= 5 (Evaluate) suggests PO3 (Design)
        if bloom_level >= 5:
            suggestions["PO3"] = {
                "weight": 2,
                "rationale": f"Bloom level {bloom_level} ({BLOOMS_LEVELS[bloom_level]}) indicates design and evaluation capabilities",
                "confidence": "high",
                "auto_suggested": True
            }
        
        # Rule 4: Bloom level 6 (Create) suggests PO4 (Complex Problem Solving)
        if bloom_level >= 6:
            suggestions["PO4"] = {
                "weight": 2,
                "rationale": f"Bloom level 6 (Create) indicates ability to solve complex, ill-structured problems",
                "confidence": "high",
                "auto_suggested": True
            }
        
        # Rule 5: Lab courses suggest PO5 (Modern Tool Usage)
        if self.is_lab:
            current = suggestions["PO5"]["weight"]
            suggestions["PO5"] = {
                "weight": max(current, 2),
                "rationale": "Lab/practical course involves use of modern engineering tools",
                "confidence": "high",
                "auto_suggested": True
            }
        
        # Rule 6: Keyword-based matching
        for po, matched_keywords in keyword_matches.items():
            current = suggestions[po]["weight"]
            keyword_boost = min(len(matched_keywords), 2)  # Max boost of 2
            
            if keyword_boost > 0:
                new_weight = min(current + keyword_boost, 3)  # Cap at 3
                if new_weight > current:
                    suggestions[po] = {
                        "weight": new_weight,
                        "rationale": f"Keywords matched: {', '.join(matched_keywords)}",
                        "confidence": "medium" if keyword_boost == 1 else "high",
                        "auto_suggested": True
                    }
        
        # Rule 7: Design keywords get extra boost for PO3
        design_keywords = ["design", "develop", "build", "create", "model", "architect"]
        statement_lower = co_statement.lower()
        if any(kw in statement_lower for kw in design_keywords):
            suggestions["PO3"]["weight"] = min(suggestions["PO3"]["weight"] + 1, 3)
            suggestions["PO3"]["rationale"] += " | Design-oriented keywords detected"
            suggestions["PO3"]["auto_suggested"] = True
        
        return suggestions
    
    def generate_matrix(self, course_outcomes: List[Dict]) -> Dict:
        """
        Generate complete CO-PO mapping matrix with AI suggestions
        
        Args:
            course_outcomes: List of CO dictionaries with 'co_id', 'statement', 'blooms_level'
            
        Returns:
            Complete mapping matrix with suggestions for each CO
        """
        matrix = {}
        
        for co in course_outcomes:
            co_id = co['co_id']
            statement = co['statement']
            bloom_level = co.get('blooms_level', self.detect_bloom_level(statement))
            
            matrix[co_id] = {
                'statement': statement,
                'blooms_level': bloom_level,
                'blooms_name': BLOOMS_LEVELS.get(bloom_level, "Unknown"),
                'mappings': self.suggest_mapping(statement, bloom_level)
            }
        
        return matrix
    
    def calculate_co_attainment(self, assessment_data: Dict) -> Dict[str, float]:
        """
        Calculate CO attainment from assessment data
        
        Args:
            assessment_data: Dictionary with CO -> {marks_obtained, max_marks}
            
        Returns:
            Dictionary with CO -> attainment percentage
        """
        attainment = {}
        
        for co_id, data in assessment_data.items():
            marks_obtained = data.get('marks_obtained', 0)
            max_marks = data.get('max_marks', 1)
            
            if max_marks > 0:
                pct = (marks_obtained / max_marks) * 100
                attainment[co_id] = {
                    'percentage': round(pct, 2),
                    'level': self._get_attainment_level(pct)
                }
            else:
                attainment[co_id] = {'percentage': 0, 'level': 0}
        
        return attainment
    
    def calculate_po_attainment(self, co_attainment: Dict, co_po_mapping: Dict) -> Dict[str, float]:
        """
        Calculate PO attainment from CO attainment and CO-PO mapping
        
        Formula: PO_j = Σ(CO_i_Attainment × Weight_ij) / Σ(Weight_ij)
        
        Args:
            co_attainment: Dictionary with CO -> attainment data
            co_po_mapping: Dictionary with CO -> {PO -> weight}
            
        Returns:
            Dictionary with PO -> attainment percentage
        """
        po_attainment = {}
        
        for po in PO_DEFINITIONS.keys():
            numerator = 0
            denominator = 0
            
            for co_id, attainment_data in co_attainment.items():
                if co_id in co_po_mapping:
                    weight = co_po_mapping[co_id].get(po, {}).get('weight', 0)
                    if weight > 0:
                        numerator += attainment_data['percentage'] * weight
                        denominator += weight
            
            if denominator > 0:
                pct = numerator / denominator
                po_attainment[po] = {
                    'percentage': round(pct, 2),
                    'level': self._get_attainment_level(pct)
                }
            else:
                po_attainment[po] = {'percentage': 0, 'level': 0}
        
        return po_attainment
    
    def _get_attainment_level(self, percentage: float) -> int:
        """
        Convert attainment percentage to level
        
        Level 3: >= 70%
        Level 2: 60-69%
        Level 1: < 60%
        """
        if percentage >= 70:
            return 3
        elif percentage >= 60:
            return 2
        else:
            return 1
    
    def get_po_definitions(self) -> Dict:
        """Return PO definitions for UI"""
        return PO_DEFINITIONS
    
    def get_blooms_levels(self) -> Dict:
        """Return Bloom's taxonomy levels for UI"""
        return BLOOMS_LEVELS


def suggest_co_po_mapping(co_statement: str, bloom_level: int = None, course_type: str = "theory") -> Dict:
    """
    Convenience function to get AI suggestions for a single CO
    
    Args:
        co_statement: The course outcome statement
        bloom_level: Bloom's taxonomy level (1-6)
        course_type: Type of course
        
    Returns:
        Mapping suggestions with rationales
    """
    engine = COPOMappingEngine(course_type)
    return engine.suggest_mapping(co_statement, bloom_level)


def generate_full_matrix(course_outcomes: List[Dict], course_type: str = "theory") -> Dict:
    """
    Generate complete CO-PO mapping matrix for a course
    
    Args:
        course_outcomes: List of CO dictionaries
        course_type: Type of course
        
    Returns:
        Complete matrix with all suggestions
    """
    engine = COPOMappingEngine(course_type)
    return engine.generate_matrix(course_outcomes)
