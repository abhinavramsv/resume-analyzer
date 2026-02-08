import re
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

def ensure_nltk_data():
    required_data = [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords', 'stopwords')
    ]
    for data_path, download_name in required_data:
        try:
            nltk.data.find(data_path)
        except LookupError:
            nltk.download(download_name, quiet=True)

ensure_nltk_data()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScoringWeights:
    skills_weight: float = 0.35
    experience_weight: float = 0.25
    education_weight: float = 0.15
    keywords_weight: float = 0.15
    summary_weight: float = 0.10

@dataclass
class MatchResult:
    overall_score: float
    skills_score: float
    experience_score: float
    education_score: float
    keywords_score: float
    summary_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    experience_gap: float
    recommendations: List[str]
    debug_info: Dict = None

class ResumeScorer:
    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()
        self.stop_words = set(stopwords.words('english'))
        self.ignore_words = self.stop_words.union({
            'experience', 'knowledge', 'skills', 'ability', 'proficiency',
            'familiar', 'understanding', 'working', 'strong', 'excellent',
            'years', 'minimum', 'development', 'programming', 'software'
        })
        self.education_hierarchy = {
            'phd': 5, 'master': 4, 'bachelor': 3, 'associate': 2, 'diploma': 2, 'certificate': 1
        }

    def safe_tokenize(self, text: str) -> List[str]:
        try:
            return word_tokenize(text)
        except:
            return re.findall(r'\b\w+\b', text.lower())

    def extract_skills_from_job_description(self, jd: str) -> List[str]:
        jd_lw = jd.lower()
        skills = set()
        patterns = [r'[•·\-\*]\s*([^•·\-\*\n]+)', r'(?:skills|requirements|qualifications)[:\s]*([^.!?\n]*)']
        
        for p in patterns:
            for m in re.finditer(p, jd_lw):
                chunk = m.group(1)
                for part in re.split(r'[,;]|\band\b|\bor\b', chunk):
                    clean = re.sub(r'[^\w\s\+#\.-]', '', part).strip()
                    if clean and clean not in self.ignore_words and not clean.isdigit():
                        skills.add(clean)
        return list(skills)

    def extract_skills_from_resume(self, parsed_resume: Dict) -> Set[str]:
        res_skills = set(s.lower() for s in parsed_resume.get('skills', []))
        raw = parsed_resume.get('raw_text', '').lower()
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\+#\.-]*\b', raw)
        for w in words:
            if w not in self.ignore_words:
                res_skills.add(w)
        return res_skills

    def calculate_match_score(self, parsed_resume: Dict, job_description: str) -> MatchResult:
        jd_skills = self.extract_skills_from_job_description(job_description)
        res_skills = self.extract_skills_from_resume(parsed_resume)
        
        matched = [s for s in jd_skills if any(s in rs or rs in s for rs in res_skills)]
        missing = [s for s in jd_skills if s not in matched]
        
        s_score = (len(matched) / len(jd_skills) * 100) if jd_skills else 50.0
        e_score = self._score_exp(parsed_resume, job_description)
        edu_score = self._score_edu(parsed_resume, job_description)
        k_score = self._score_keywords(parsed_resume, job_description)
        sum_score = self._score_summary(parsed_resume, job_description)

        overall = (s_score * self.weights.skills_weight + 
                   e_score * self.weights.experience_weight + 
                   edu_score * self.weights.education_weight + 
                   k_score * self.weights.keywords_weight + 
                   sum_score * self.weights.summary_weight)

        return MatchResult(
            overall_score=round(overall, 2),
            skills_score=round(s_score, 2),
            experience_score=round(e_score, 2),
            education_score=round(edu_score, 2),
            keywords_score=round(k_score, 2),
            summary_score=round(sum_score, 2),
            matched_skills=matched,
            missing_skills=missing,
            experience_gap=0.0,
            recommendations=self._gen_recs(s_score, e_score)
        )

    def _score_exp(self, resume: Dict, jd: str) -> float:
        res_years = resume.get('total_experience_years', 0) or 0
        match = re.search(r'(\d+)\s*[\+\s]*years?', jd.lower())
        req_years = int(match.group(1)) if match else 0
        if req_years == 0: return 80.0
        return min(100, (res_years / req_years) * 80) if res_years < req_years else 100.0

    def _score_edu(self, resume: Dict, jd: str) -> float:
        edu_list = resume.get('education', [])
        if not edu_list: return 40.0
        return 90.0 if any(k in jd.lower() for k in ['degree', 'bachelor', 'master']) else 70.0

    def _score_keywords(self, resume: Dict, jd: str) -> float:
        res_text = str(resume.get('skills', [])) + str(resume.get('summary', ''))
        jd_tokens = set(self.safe_tokenize(jd.lower()))
        res_tokens = set(self.safe_tokenize(res_text.lower()))
        overlap = jd_tokens.intersection(res_tokens) - self.ignore_words
        return min(100, len(overlap) * 5)

    def _score_summary(self, resume: Dict, jd: str) -> float:
        return 85.0 if resume.get('summary') else 50.0

    def _gen_recs(self, s_score: float, e_score: float) -> List[str]:
        recs = []
        if s_score < 60: recs.append("Add more technical skills found in the job post.")
        if e_score < 60: recs.append("Highlight more relevant work experience.")
        return recs or ["Strong profile match."]
