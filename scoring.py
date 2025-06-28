"""
Simple Resume Scoring Module - Direct Skills Matching
Compares skills mentioned in job description with resume skills directly
"""

import re
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download required NLTK data
def ensure_nltk_data():
    """Ensure all required NLTK data is downloaded"""
    required_data = [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords', 'stopwords')
    ]
    
    for data_path, download_name in required_data:
        try:
            nltk.data.find(data_path)
        except LookupError:
            print(f"Downloading {download_name}...")
            nltk.download(download_name, quiet=True)

ensure_nltk_data()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScoringWeights:
    """Configuration for scoring algorithm weights"""
    skills_weight: float = 0.35
    experience_weight: float = 0.25
    education_weight: float = 0.15
    keywords_weight: float = 0.15
    summary_weight: float = 0.10

@dataclass
class MatchResult:
    """Container for match scoring results"""
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

class ResumeScorer:  # Changed from SimpleResumeScorer to ResumeScorer
    """
    Simple resume scoring system that directly matches skills from job description to resume
    """
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()
        
        # Initialize stopwords with error handling
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            print("Downloading stopwords...")
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        
        # Add common non-skill words to ignore
        self.ignore_words = self.stop_words.union({
            'experience', 'knowledge', 'skills', 'ability', 'proficiency',
            'familiar', 'understanding', 'working', 'strong', 'excellent',
            'good', 'basic', 'advanced', 'expert', 'years', 'year',
            'plus', 'bonus', 'preferred', 'required', 'must', 'should',
            'including', 'such', 'like', 'using', 'with', 'of', 'in',
            'and', 'or', 'the', 'a', 'an', 'to', 'for', 'on', 'at',
            'minimum', 'maximum', 'least', 'development', 'programming',
            'software', 'application', 'system', 'technology', 'tool',
            'framework', 'library', 'platform', 'environment'
        })
        
        # Experience level mappings
        self.experience_levels = {
            'entry': (0, 2),
            'junior': (1, 3),
            'mid': (3, 7),
            'senior': (7, 12),
            'principal': (10, float('inf')),
            'lead': (5, float('inf'))
        }
        
        # Education level hierarchy
        self.education_hierarchy = {
            'phd': 5, 'doctorate': 5, 'doctoral': 5,
            'master': 4, 'masters': 4, 'msc': 4, 'mba': 4,
            'bachelor': 3, 'bachelors': 3, 'bsc': 3, 'ba': 3,
            'associate': 2, 'diploma': 2,
            'certificate': 1, 'certification': 1
        }
    
    def safe_tokenize(self, text: str) -> List[str]:
        """Tokenize text with fallback for NLTK issues"""
        try:
            return word_tokenize(text)
        except Exception as e:
            logger.warning(f"NLTK tokenization failed: {e}. Using simple split.")
            return re.findall(r'\b\w+\b', text.lower())
    
    def extract_skills_from_job_description(self, job_description: str) -> List[str]:
        """Extract potential skills from job description"""
        jd_lower = job_description.lower()
        
        # Look for skills in common sections
        skill_patterns = [
            # Technical skills sections
            r'(?:technical skills|required skills|skills|qualifications|requirements)[:\s]*([^.!?\n]*(?:\n[^.!?\n]*)*?)(?:\n\s*\n|\n[A-Z]|$)',
            r'(?:experience with|proficiency in|knowledge of|familiar with)[:\s]*([^.!?\n]*)',
            r'(?:must have|required|essential)[:\s]*([^.!?\n]*)',
            
            # Bullet points (common in job descriptions)
            r'[•·\-\*]\s*([^•·\-\*\n]+)',
            
            # Parenthetical mentions
            r'\(([^)]+)\)',
            
            # "X years of experience in Y" patterns
            r'\d+\+?\s*years?\s+(?:of\s+)?(?:experience\s+)?(?:in|with|using)\s+([^,.!?\n]+)',
        ]
        
        extracted_text_chunks = []
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, jd_lower, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                matched_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if matched_text and len(matched_text.strip()) > 2:
                    extracted_text_chunks.append(matched_text.strip())
        
        # Extract individual skills from the chunks
        potential_skills = set()
        
        for chunk in extracted_text_chunks:
            # Clean the chunk
            cleaned_chunk = re.sub(r'[,;()&/\|]', ' ', chunk)
            cleaned_chunk = re.sub(r'\s+', ' ', cleaned_chunk).strip()
            
            # Split by common separators and extract skills
            parts = re.split(r'\s+(?:and|or|\+|,|;)\s+', cleaned_chunk)
            
            for part in parts:
                part = part.strip()
                if len(part) > 1:
                    # Extract meaningful words/phrases
                    words = part.split()
                    
                    # Single word skills
                    for word in words:
                        word = re.sub(r'[^\w\+#\.-]', '', word)
                        if (len(word) > 1 and 
                            word.lower() not in self.ignore_words and
                            not word.isdigit()):
                            potential_skills.add(word.lower())
                    
                    # Multi-word skills (2-3 words max)
                    if len(words) <= 3 and len(part) <= 50:
                        clean_part = re.sub(r'[^\w\s\+#\.-]', '', part).strip()
                        if (clean_part and 
                            len(clean_part) > 2 and 
                            not any(word in self.ignore_words for word in clean_part.lower().split())):
                            potential_skills.add(clean_part.lower())
        
        # Also look for common technology patterns throughout the text
        tech_patterns = [
            r'\b[a-zA-Z][a-zA-Z0-9]*\.js\b',  # JavaScript frameworks
            r'\b[a-zA-Z]+\+\+\b',  # C++, etc.
            r'\b[a-zA-Z]+#\b',     # C#, F#, etc.
            r'\b[a-zA-Z]{2,}\.[a-zA-Z]{2,}\b',  # dotted technologies
            r'\b[A-Z]{2,}\b',      # Acronyms
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, job_description)
            for match in matches:
                if match.lower() not in self.ignore_words:
                    potential_skills.add(match.lower())
        
        return list(potential_skills)
    
    def extract_skills_from_resume(self, parsed_resume: Dict) -> Set[str]:
        """Extract all potential skills from resume"""
        resume_skills = set()
        
        # Get skills from the parsed skills section
        for skill in parsed_resume.get('skills', []):
            resume_skills.add(skill.lower().strip())
        
        # Also extract from full resume text
        resume_text_parts = [
            parsed_resume.get('summary', ''),
            ' '.join([exp.get('title', '') + ' ' + exp.get('context', '') for exp in parsed_resume.get('experience', [])]),
            ' '.join([edu.get('institution', '') + ' ' + edu.get('context', '') for edu in parsed_resume.get('education', [])]),
            parsed_resume.get('raw_text', '')
        ]
        
        full_resume_text = ' '.join(resume_text_parts).lower()
        
        # Extract potential skills from resume text using similar patterns
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\+#\.-]*\b', full_resume_text)
        for word in words:
            if (len(word) > 1 and 
                word.lower() not in self.ignore_words and
                not word.isdigit()):
                resume_skills.add(word.lower())
        
        return resume_skills
    
    def calculate_skill_similarity(self, skill1: str, skill2: str) -> float:
        """Calculate similarity between two skills"""
        skill1, skill2 = skill1.lower(), skill2.lower()
        
        # Exact match
        if skill1 == skill2:
            return 1.0
        
        # One contains the other
        if skill1 in skill2 or skill2 in skill1:
            return 0.9
        
        # Character-based similarity for close matches
        set1 = set(skill1)
        set2 = set(skill2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        char_similarity = intersection / union if union > 0 else 0
        
        # Word-based similarity for multi-word skills
        words1 = skill1.split()
        words2 = skill2.split()
        if len(words1) > 1 or len(words2) > 1:
            common_words = set(words1).intersection(set(words2))
            total_words = set(words1).union(set(words2))
            word_similarity = len(common_words) / len(total_words) if total_words else 0
            return max(char_similarity, word_similarity)
        
        return char_similarity
    
    def score_skills_direct_match(self, parsed_resume: Dict, job_description: str) -> Dict:
        """Score skills by directly comparing job description skills with resume skills"""
        
        # Extract skills from both sources
        job_skills = self.extract_skills_from_job_description(job_description)
        resume_skills = self.extract_skills_from_resume(parsed_resume)
        
        if not job_skills:
            return {
                'score': 50.0,
                'matched': [],
                'missing': job_skills,
                'debug': {
                    'job_skills_found': 0,
                    'resume_skills_found': len(resume_skills),
                    'reason': 'No skills extracted from job description'
                }
            }
        
        # Find matches
        matched_skills = []
        missing_skills = []
        
        for job_skill in job_skills:
            best_match = None
            best_similarity = 0
            
            for resume_skill in resume_skills:
                similarity = self.calculate_skill_similarity(job_skill, resume_skill)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = resume_skill
            
            # Consider it a match if similarity is above threshold
            if best_similarity >= 0.7:  # Adjustable threshold
                matched_skills.append(job_skill)
            else:
                missing_skills.append(job_skill)
        
        # Calculate score
        match_rate = len(matched_skills) / len(job_skills)
        
        # Base score from match rate
        base_score = match_rate * 85  # Up to 85 points
        
        # Bonus for having many skills (even if not all required)
        skill_abundance_bonus = min(15, len(resume_skills) / max(1, len(job_skills)) * 10)
        
        total_score = min(100, base_score + skill_abundance_bonus)
        
        debug_info = {
            'job_skills_found': len(job_skills),
            'resume_skills_found': len(resume_skills),
            'job_skills': job_skills[:10],  # Show first 10 for debugging
            'resume_skills_sample': list(resume_skills)[:10],
            'match_rate': match_rate,
            'base_score': base_score,
            'skill_abundance_bonus': skill_abundance_bonus
        }
        
        return {
            'score': total_score,
            'matched': matched_skills,
            'missing': missing_skills,
            'debug': debug_info
        }
    
    def _score_experience(self, parsed_resume: Dict, job_requirements: Dict) -> Dict:
        """Score experience match"""
        resume_experience = parsed_resume.get('total_experience_years', 0) or 0
        required_experience = job_requirements.get('min_experience', 0)
        
        if required_experience == 0:
            return {'score': 75.0, 'gap': 0}
        
        if resume_experience >= required_experience:
            bonus = min(25, (resume_experience - required_experience) * 5)
            score = min(100, 75 + bonus)
        else:
            gap = required_experience - resume_experience
            penalty = gap * 15
            score = max(0, 75 - penalty)
        
        return {
            'score': score,
            'gap': max(0, required_experience - resume_experience)
        }
    
    def _score_education(self, parsed_resume: Dict, job_requirements: Dict) -> Dict:
        """Score education match"""
        education_data = parsed_resume.get('education', [])
        required_education = job_requirements.get('education_requirement')
        
        if not required_education:
            return {'score': 75.0}
        
        if not education_data:
            return {'score': 30.0}
        
        highest_level = 0
        for edu in education_data:
            edu_text = edu.get('institution', '').lower() + ' ' + edu.get('context', '').lower()
            for level, value in self.education_hierarchy.items():
                if level in edu_text:
                    highest_level = max(highest_level, value)
        
        required_level = self.education_hierarchy.get(required_education.lower(), 0)
        
        if highest_level >= required_level:
            bonus = (highest_level - required_level) * 10
            score = min(100, 80 + bonus)
        else:
            penalty = (required_level - highest_level) * 20
            score = max(20, 80 - penalty)
        
        return {'score': score}
    
    def _score_keywords(self, parsed_resume: Dict, job_description: str) -> Dict:
        """Score based on keyword overlap"""
        resume_text = (
            ' '.join(parsed_resume.get('skills', [])) + ' ' +
            str(parsed_resume.get('summary', '')) + ' ' +
            ' '.join([exp.get('title', '') for exp in parsed_resume.get('experience', [])])
        ).lower()
        
        jd_text = job_description.lower()
        
        resume_tokens = set(self._clean_tokens(self.safe_tokenize(resume_text)))
        jd_tokens = set(self._clean_tokens(self.safe_tokenize(jd_text)))
        
        if not jd_tokens:
            return {'score': 50.0}
        
        overlap = len(resume_tokens.intersection(jd_tokens))
        union = len(resume_tokens.union(jd_tokens))
        
        jaccard_score = (overlap / union) * 100 if union > 0 else 0
        return {'score': min(100, jaccard_score * 2)}
    
    def _score_summary(self, parsed_resume: Dict, job_description: str) -> Dict:
        """Score relevance of resume summary to job description"""
        summary = parsed_resume.get('summary', '')
        
        if not summary:
            return {'score': 50.0}
        
        summary_lower = summary.lower()
        jd_lower = job_description.lower()
        
        jd_tokens = set(self._clean_tokens(self.safe_tokenize(jd_lower)))
        summary_tokens = set(self._clean_tokens(self.safe_tokenize(summary_lower)))
        
        if not jd_tokens:
            return {'score': 50.0}
        
        overlap = len(summary_tokens.intersection(jd_tokens))
        relevance_score = (overlap / len(jd_tokens)) * 100
        
        return {'score': min(100, relevance_score * 3)}
    
    def _clean_tokens(self, tokens: List[str]) -> List[str]:
        """Clean and filter tokens"""
        return [
            token for token in tokens
            if (len(token) > 2 and 
                token.isalpha() and 
                token not in self.stop_words)
        ]
    
    def _parse_job_description_simple(self, job_description: str) -> Dict:
        """Simple job description parsing for experience and education"""
        jd_lower = job_description.lower()
        
        # Extract experience requirements
        exp_patterns = [
            r'(\d+)[\+\s]*years?\s+(?:of\s+)?(?:experience|exp)',
            r'minimum\s+(\d+)\s+years?',
            r'(\d+)[\+\s]*years?\s+(?:in|with|of)',
            r'(\d+)\+\s*years?'
        ]
        
        min_experience = 0
        for pattern in exp_patterns:
            matches = re.findall(pattern, jd_lower)
            if matches:
                min_experience = max(min_experience, int(matches[0]))
        
        # Extract education requirements
        education_requirement = None
        for edu_level in self.education_hierarchy.keys():
            if edu_level in jd_lower:
                if not education_requirement or self.education_hierarchy[edu_level] > self.education_hierarchy.get(education_requirement, 0):
                    education_requirement = edu_level
        
        return {
            'min_experience': min_experience,
            'education_requirement': education_requirement,
            'full_text': job_description
        }
    
    def calculate_match_score(self, parsed_resume: Dict, job_description: str, 
                            required_skills: List[str] = None, 
                            preferred_skills: List[str] = None,
                            min_experience: float = None,
                            education_requirement: str = None) -> MatchResult:
        """
        Calculate comprehensive match score with direct skills matching
        """
        try:
            # Parse job description for basic requirements
            job_requirements = self._parse_job_description_simple(job_description)
            
            # Override with explicit requirements if provided
            if min_experience is not None:
                job_requirements['min_experience'] = min_experience
            if education_requirement:
                job_requirements['education_requirement'] = education_requirement
            
            # Calculate individual scores using direct matching for skills
            skills_result = self.score_skills_direct_match(parsed_resume, job_description)
            experience_result = self._score_experience(parsed_resume, job_requirements)
            education_result = self._score_education(parsed_resume, job_requirements)
            keywords_result = self._score_keywords(parsed_resume, job_description)
            summary_result = self._score_summary(parsed_resume, job_description)
            
            # Calculate weighted overall score
            overall_score = (
                skills_result['score'] * self.weights.skills_weight +
                experience_result['score'] * self.weights.experience_weight +
                education_result['score'] * self.weights.education_weight +
                keywords_result['score'] * self.weights.keywords_weight +
                summary_result['score'] * self.weights.summary_weight
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                skills_result, experience_result, education_result, 
                keywords_result, summary_result
            )
            
            return MatchResult(
                overall_score=round(overall_score, 2),
                skills_score=round(skills_result['score'], 2),
                experience_score=round(experience_result['score'], 2),
                education_score=round(education_result['score'], 2),
                keywords_score=round(keywords_result['score'], 2),
                summary_score=round(summary_result['score'], 2),
                matched_skills=skills_result['matched'],
                missing_skills=skills_result['missing'],
                experience_gap=experience_result.get('gap', 0),
                recommendations=recommendations,
                debug_info=skills_result.get('debug', {})
            )
            
        except Exception as e:
            logger.error(f"Error calculating match score: {str(e)}")
            return self._create_error_result(str(e))
    
    def _generate_recommendations(self, skills_result: Dict, experience_result: Dict, 
                                education_result: Dict, keywords_result: Dict, 
                                summary_result: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if skills_result['score'] < 60:
            missing_count = len(skills_result['missing'])
            if missing_count > 0:
                recommendations.append(
                    f"Skills gap identified. Missing {missing_count} key skills: {', '.join(skills_result['missing'][:3])}{'...' if missing_count > 3 else ''}"
                )
        
        if experience_result['score'] < 60 and experience_result.get('gap', 0) > 0:
            recommendations.append(
                f"Experience gap: {experience_result['gap']:.1f} years below requirement"
            )
        
        if education_result['score'] < 60:
            recommendations.append("Education level may not meet job requirements")
        
        if keywords_result['score'] < 50:
            recommendations.append("Resume could better match job description keywords")
        
        if summary_result['score'] < 50:
            recommendations.append("Professional summary could be more aligned with job requirements")
        
        if not recommendations:
            recommendations.append("Strong candidate match across all criteria")
        
        return recommendations
    
    def _create_error_result(self, error_message: str) -> MatchResult:
        """Create a default result for error cases"""
        return MatchResult(
            overall_score=0.0,
            skills_score=0.0,
            experience_score=0.0,
            education_score=0.0,
            keywords_score=0.0,
            summary_score=0.0,
            matched_skills=[],
            missing_skills=[],
            experience_gap=0.0,
            recommendations=[f"Error in scoring: {error_message}"]
        )

# Example usage:
if __name__ == "__main__":
    scorer = ResumeScorer()  # Changed from SimpleResumeScorer to ResumeScorer
    print("ResumeScorer initialized successfully!")
    
    # Test with sample data
    sample_resume = {
        'skills': ['Python', 'JavaScript', 'React', 'SQL'],
        'total_experience_years': 5,
        'summary': 'Experienced software developer with expertise in web development',
        'experience': [],
        'education': []
    }
    
    sample_job = """
    We are looking for a Software Developer with:
    - 3+ years of experience
    - Python programming
    - JavaScript and React
    - Database knowledge (SQL)
    - Experience with web development
    """
    
    result = scorer.calculate_match_score(sample_resume, sample_job)
    print(f"Sample match score: {result.overall_score}%")
    print(f"Skills score: {result.skills_score}%")
    print(f"Matched skills: {result.matched_skills}")
    print(f"Missing skills: {result.missing_skills}")
    if result.debug_info:
        print(f"Debug info: {result.debug_info}")