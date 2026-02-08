import re
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
import PyPDF2
import docx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self):
        self.skills_db = [
            'python', 'java', 'javascript', 'c++', 'sql', 'html', 'css', 'typescript',
            'react', 'angular', 'vue', 'django', 'flask', 'tensorflow', 'pytorch',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'linux', 'agile'
        ]
        self.edu_keys = ['bachelor', 'master', 'phd', 'degree', 'university', 'college']

    def parse_resume(self, file_path: Union[str, Path]) -> Dict:
        try:
            path = Path(file_path)
            text = self._extract_text(path)
            
            return {
                'file_name': path.name,
                'parsed_at': datetime.now().isoformat(),
                'contact': self._extract_contact(text),
                'skills': self._extract_skills(text),
                'experience': self._extract_exp(text),
                'education': self._extract_edu(text),
                'summary': self._extract_summary(text),
                'total_exp': self._calc_years(text)
            }
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return {'error': str(e)}

    def _extract_text(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext == '.pdf':
            text = ""
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        elif ext == '.docx':
            doc = docx.Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext == '.txt':
            return path.read_text(encoding='utf-8')
        raise ValueError("Unsupported format")

    def _extract_contact(self, text: str) -> Dict:
        email = re.findall(r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b', text)
        phone = re.findall(r'(\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}', text)
        return {
            'email': email[0] if email else None,
            'phone': phone[0] if phone else None
        }

    def _extract_skills(self, text: str) -> List[str]:
        found = []
        text_lw = text.lower()
        for skill in self.skills_db:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lw):
                found.append(skill)
        return list(set(found))

    def _extract_exp(self, text: str) -> List[Dict]:
        exp = []
        roles = ['developer', 'engineer', 'manager', 'analyst', 'specialist']
        for i, line in enumerate(text.split('\n')):
            if any(r in line.lower() for r in roles):
                exp.append({'title': line.strip(), 'snippet': text.split('\n')[i:i+2]})
        return exp[:5]

    def _extract_edu(self, text: str) -> List[Dict]:
        edu = []
        for line in text.split('\n'):
            if any(k in line.lower() for k in self.edu_keys):
                edu.append({'info': line.strip()})
        return edu[:3]

    def _extract_summary(self, text: str) -> Optional[str]:
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(k in line.lower() for k in ['summary', 'objective', 'profile']):
                return " ".join([l.strip() for l in lines[i+1:i+4] if l.strip()])
        return lines[0].strip() if len(lines[0]) > 20 else None

    def _calc_years(self, text: str) -> Optional[float]:
        matches = re.findall(r'(\d+)[\+\s]*years?', text.lower())
        if matches:
            return float(max(matches))
        
        dates = re.findall(r'(\d{4})\s*[-–—]\s*(\d{4}|present)', text.lower())
        total = 0
        curr = datetime.now().year
        for start, end in dates:
            y_start = int(start)
            y_end = curr if end == 'present' else int(end)
            total += max(0, y_end - y_start)
        return total if total > 0 else None
