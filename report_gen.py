import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ReportConfig:
    include_detailed_analysis: bool = True
    include_recommendations: bool = True
    include_skills_breakdown: bool = True
    report_format: str = "detailed"

class ReportGenerator:
    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self.quality_levels = {
            'excellent': (85, 100, "Excellent Match"),
            'good': (70, 84, "Good Match"),
            'moderate': (55, 69, "Moderate Match"),
            'weak': (40, 54, "Weak Match"),
            'poor': (0, 39, "Poor Match")
        }

    def generate_comprehensive_report(self, match_result: Any, parsed_resume: Dict,
                                    job_description: str, candidate_name: str = "Candidate",
                                    job_title: str = "Position", 
                                    recruiter_name: str = "Recruiter") -> Dict[str, str]:
        try:
            data = self._prepare_report_data(
                match_result, parsed_resume, job_description, 
                candidate_name, job_title, recruiter_name
            )
            
            reports = {
                'executive_summary': self._generate_executive_summary(data),
                'detailed_analysis': self._generate_detailed_analysis(data),
                'hiring_recommendation': self._generate_hiring_recommendation(data),
                'interview_guide': self._generate_interview_guide(data),
                'feedback_report': self._generate_candidate_feedback(data)
            }
            
            reports['full_report'] = self._generate_full_report(reports, data)
            return reports
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {'error': str(e)}

    def _prepare_report_data(self, match_result: Any, parsed_resume: Dict,
                           job_description: str, candidate_name: str,
                           job_title: str, recruiter_name: str) -> Dict:
        
        scores = {
            'Skills': match_result.skills_score,
            'Experience': match_result.experience_score,
            'Education': match_result.education_score,
            'Keywords': match_result.keywords_score,
            'Summary': match_result.summary_score
        }
        
        return {
            'candidate_name': candidate_name,
            'job_title': job_title,
            'recruiter_name': recruiter_name,
            'analysis_date': datetime.now().strftime('%B %d, %Y'),
            'analysis_time': datetime.now().strftime('%I:%M %p'),
            'match_result': match_result,
            'parsed_resume': parsed_resume,
            'quality_level': self._get_quality_level(match_result.overall_score),
            'strengths': [k for k, v in scores.items() if v >= 75],
            'weaknesses': [k for k, v in scores.items() if v < 60],
            'top_skills': match_result.matched_skills[:10],
            'missing_skills': match_result.missing_skills[:8],
            'key_recommendations': match_result.recommendations[:5]
        }

    def _generate_executive_summary(self, data: Dict) -> str:
        return f"""
EXECUTIVE SUMMARY
{'=' * 30}
Candidate: {data['candidate_name']}
Position: {data['job_title']}
Assessment: {data['quality_level'][2]} ({data['match_result'].overall_score:.1f}%)

KEY FINDINGS:
• Strongest areas: {', '.join(data['strengths']) if data['strengths'] else 'None'}
• Areas for improvement: {', '.join(data['weaknesses']) if data['weaknesses'] else 'None'}
• Skills: {len(data['top_skills'])} matched, {len(data['missing_skills'])} missing

RECOMMENDATION: {self._get_hiring_recommendation(data['match_result'].overall_score)}
"""

    def _generate_detailed_analysis(self, data: Dict) -> str:
        res = data['parsed_resume']
        return f"""
DETAILED ANALYSIS
{'=' * 30}
1. SKILLS ({data['match_result'].skills_score:.1f}%)
   Matched: {', '.join(data['top_skills'])}
   Missing: {', '.join(data['missing_skills'])}

2. EXPERIENCE ({data['match_result'].experience_score:.1f}%)
   Total Years: {res.get('total_experience_years', 'N/A')}
   
3. EDUCATION ({data['match_result'].education_score:.1f}%)
   {self._format_education(res.get('education', []))}
"""

    def _generate_hiring_recommendation(self, data: Dict) -> str:
        score = data['match_result'].overall_score
        return f"""
HIRING RECOMMENDATION
{'=' * 30}
Decision: {self._get_hiring_recommendation(score)}

RISK ASSESSMENT:
{self._assess_hiring_risks(data)}

FINAL VERDICT:
{self._get_final_recommendation(data)}
"""

    def _generate_interview_guide(self, data: Dict) -> str:
        return f"""
INTERVIEW GUIDE
{'=' * 30}
TECHNICAL QUESTIONS:
{self._generate_technical_questions(data)}

RED FLAGS:
{self._format_list(self._get_red_flags(data), '⚠ ')}
"""

    def _generate_candidate_feedback(self, data: Dict) -> str:
        return f"""
CANDIDATE FEEDBACK
{'=' * 30}
Dear {data['candidate_name']},
Your match score: {data['match_result'].overall_score:.1f}%

STRENGTHS:
{self._format_list(data['strengths'], '✅ ')}

RECOMMENDATIONS:
{self._format_list(data['key_recommendations'], '💡 ')}
"""

    def _generate_full_report(self, reports: Dict, data: Dict) -> str:
        return f"""
COMPREHENSIVE ANALYSIS REPORT
{'=' * 45}
{reports['executive_summary']}
{'-' * 45}
{reports['detailed_analysis']}
{'-' * 45}
{reports['hiring_recommendation']}
{'-' * 45}
{reports['interview_guide']}
"""

    def _get_quality_level(self, score: float) -> Tuple[int, int, str]:
        for level, (low, high, desc) in self.quality_levels.items():
            if low <= score <= high: return (low, high, desc)
        return (0, 39, "Poor Match")

    def _get_hiring_recommendation(self, score: float) -> str:
        if score >= 85: return "STRONG HIRE"
        if score >= 70: return "HIRE"
        if score >= 55: return "CONDITIONAL"
        return "DO NOT HIRE"

    def _assess_hiring_risks(self, data: Dict) -> str:
        risks = []
        if data['match_result'].overall_score < 60: risks.append("• High training overhead")
        if len(data['missing_skills']) > 3: risks.append("• Significant skill gaps")
        return "\n".join(risks) if risks else "• Low risk"

    def _get_final_recommendation(self, data: Dict) -> str:
        score = data['match_result'].overall_score
        if score >= 85: return "Proceed with offer immediately."
        if score >= 70: return "Move to final interview rounds."
        return "Consider alternative candidates."

    def _generate_technical_questions(self, data: Dict) -> str:
        qs = [f"• Tell us about your experience with {s}" for s in data['top_skills'][:3]]
        return "\n".join(qs)

    def _get_red_flags(self, data: Dict) -> List[str]:
        flags = []
        if data['match_result'].overall_score < 40: flags.append("Low overall score")
        return flags or ["No major flags"]

    def _format_list(self, items: List[str], prefix: str = '• ') -> str:
        return '\n'.join([f"{prefix}{i}" for i in items]) if items else f"{prefix}None"

    def _format_education(self, edu: List[Dict]) -> str:
        return '\n'.join([f"• {e.get('institution', 'N/A')}" for e in edu[:2]]) if edu else "None listed"

    def export_to_file(self, content: str, filename: str) -> str:
        path = Path(f"{filename}.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(path)
