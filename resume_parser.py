"""
Resume Parser Module
Extracts and parses key information from resumes in various formats (PDF, DOCX, TXT)
"""

import re
import os
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
import PyPDF2
import docx
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeParser:
    """
    A comprehensive resume parser that extracts structured information from resumes
    """
    
    def __init__(self):
        self.skills_database = self._load_skills_database()
        self.education_keywords = ['bachelor', 'master', 'phd', 'doctorate', 'diploma', 'certificate', 
                                 'degree', 'university', 'college', 'institute', 'school']
        self.experience_keywords = ['experience', 'work', 'employment', 'career', 'position', 
                                  'role', 'job', 'professional']
    
    def _load_skills_database(self) -> List[str]:
        """Load a comprehensive list of technical skills"""
        return [
            # Programming Languages
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'go', 'rust', 'scala', 'r', 'matlab', 'sql', 'html', 'css', 'typescript',
            
            # Frameworks & Libraries
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'node.js', 'express',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'bootstrap',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 'sqlite',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'gitlab',
            'terraform', 'ansible', 'puppet', 'chef',
            
            # Other Technologies
            'linux', 'windows', 'macos', 'agile', 'scrum', 'jira', 'confluence'
        ]
    
    def parse_resume(self, file_path: Union[str, Path]) -> Dict:
        """
        Main method to parse resume and extract structured information
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            Dictionary containing parsed resume information
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Resume file not found: {file_path}")
            
            # Extract text based on file type
            text = self._extract_text(file_path)
            
            # Parse different sections
            parsed_data = {
                'file_name': file_path.name,
                'parsed_date': datetime.now().isoformat(),
                'contact_info': self._extract_contact_info(text),
                'skills': self._extract_skills(text),
                'experience': self._extract_experience(text),
                'education': self._extract_education(text),
                'summary': self._extract_summary(text),
                'raw_text': text[:1000],  # Store first 1000 chars for reference
                'total_experience_years': self._calculate_experience_years(text)
            }
            
            logger.info(f"Successfully parsed resume: {file_path.name}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume {file_path}: {str(e)}")
            return {'error': str(e), 'file_name': str(file_path)}
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from different file formats"""
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self._extract_from_pdf(file_path)
        elif extension == '.docx':
            return self._extract_from_docx(file_path)
        elif extension == '.txt':
            return self._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF files"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise
        return text
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX files"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error reading DOCX: {e}")
            raise
        return text
    
    def _extract_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            logger.error(f"Error reading TXT: {e}")
            raise
        return text
    
    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information from resume text"""
        contact_info = {}
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['email'] = emails[0] if emails else None
        
        # Phone number extraction
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        contact_info['phone'] = phones[0] if phones else None
        
        # LinkedIn profile extraction
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.findall(linkedin_pattern, text.lower())
        contact_info['linkedin'] = linkedin[0] if linkedin else None
        
        return contact_info
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.skills_database:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience information"""
        experience = []
        
        # Look for date patterns that might indicate employment periods
        date_pattern = r'(\d{4})\s*[-–—]\s*(\d{4}|present|current)'
        dates = re.findall(date_pattern, text.lower())
        
        # Look for job titles and company names (simplified approach)
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['manager', 'developer', 'engineer', 'analyst', 'specialist']):
                experience.append({
                    'title': line,
                    'context': ' '.join(lines[max(0, i-1):i+3])  # Include surrounding context
                })
        
        return experience[:5]  # Limit to top 5 experiences
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in self.education_keywords):
                education.append({
                    'institution': line.strip(),
                    'context': ' '.join(lines[max(0, i-1):i+2])
                })
        
        return education[:3]  # Limit to top 3 education entries
    
    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary or objective"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['summary', 'objective', 'profile', 'about']):
                # Get the next few lines as summary
                summary_lines = []
                for j in range(i+1, min(i+5, len(lines))):
                    if lines[j].strip():
                        summary_lines.append(lines[j].strip())
                    else:
                        break
                
                if summary_lines:
                    return ' '.join(summary_lines)
        
        # If no explicit summary found, use first substantial paragraph
        for line in lines[:10]:
            if len(line.strip()) > 50 and not any(char.isdigit() for char in line[:20]):
                return line.strip()
        
        return None
    
    def _calculate_experience_years(self, text: str) -> Optional[float]:
        """Calculate total years of experience from resume"""
        # Look for explicit experience mentions
        exp_pattern = r'(\d+)[\+\s]*years?\s+(?:of\s+)?experience'
        matches = re.findall(exp_pattern, text.lower())
        
        if matches:
            return float(max(matches))  # Return the highest mentioned experience
        
        # Alternative: count date ranges
        date_pattern = r'(\d{4})\s*[-–—]\s*(\d{4}|present|current)'
        dates = re.findall(date_pattern, text.lower())
        
        total_years = 0
        current_year = datetime.now().year
        
        for start, end in dates:
            start_year = int(start)
            end_year = current_year if end in ['present', 'current'] else int(end)
            total_years += max(0, end_year - start_year)
        
        return total_years if total_years > 0 else None

# Production usage example:
# parser = ResumeParser()
# parsed_resume = parser.parse_resume("/path/to/candidate_resume.pdf")
# This will extract all relevant information from real candidate resumes