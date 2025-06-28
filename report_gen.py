"""
Report Generator Module
Creates comprehensive written reports for resume analysis results
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from dataclasses import dataclass
import json
from pathlib import Path
import textwrap
from jinja2 import Template
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ReportConfig:
    """Configuration for report generation"""
    include_detailed_analysis: bool = True
    include_recommendations: bool = True
    include_skills_breakdown: bool = True
    include_comparative_analysis: bool = False
    executive_summary_only: bool = False
    report_format: str = "detailed"  # "detailed", "summary", "executive"

class ReportGenerator:
    """
    Generates comprehensive reports for resume analysis results
    """
    
    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self.report_templates = self._load_templates()
        
        # Report quality thresholds
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
        """
        Generate a comprehensive analysis report
        
        Args:
            match_result: MatchResult object from scoring.py
            parsed_resume: Parsed resume data from resume_parser.py
            job_description: Original job description text
            candidate_name: Name of the candidate
            job_title: Job position title
            recruiter_name: Name of the recruiter
            
        Returns:
            Dictionary containing different report formats
        """
        try:
            report_data = self._prepare_report_data(
                match_result, parsed_resume, job_description, 
                candidate_name, job_title, recruiter_name
            )
            
            reports = {}
            
            # Generate different report formats
            reports['executive_summary'] = self._generate_executive_summary(report_data)
            reports['detailed_analysis'] = self._generate_detailed_analysis(report_data)
            reports['hiring_recommendation'] = self._generate_hiring_recommendation(report_data)
            reports['interview_guide'] = self._generate_interview_guide(report_data)
            reports['feedback_report'] = self._generate_candidate_feedback(report_data)
            
            # Generate combined report
            reports['full_report'] = self._generate_full_report(reports, report_data)
            
            logger.info(f"Comprehensive report generated for {candidate_name}")
            return reports
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {'error': f"Report generation failed: {str(e)}"}
    
    def _prepare_report_data(self, match_result: Any, parsed_resume: Dict,
                           job_description: str, candidate_name: str,
                           job_title: str, recruiter_name: str) -> Dict:
        """Prepare structured data for report generation"""
        
        # Determine overall quality level
        quality_level = self._get_quality_level(match_result.overall_score)
        
        # Calculate strengths and weaknesses
        component_scores = {
            'Skills': match_result.skills_score,
            'Experience': match_result.experience_score,
            'Education': match_result.education_score,
            'Keywords': match_result.keywords_score,
            'Summary': match_result.summary_score
        }
        
        strengths = [k for k, v in component_scores.items() if v >= 75]
        weaknesses = [k for k, v in component_scores.items() if v < 60]
        
        return {
            'candidate_name': candidate_name,
            'job_title': job_title,
            'recruiter_name': recruiter_name,
            'analysis_date': datetime.now().strftime('%B %d, %Y'),
            'analysis_time': datetime.now().strftime('%I:%M %p'),
            'match_result': match_result,
            'parsed_resume': parsed_resume,
            'job_description': job_description[:500] + "..." if len(job_description) > 500 else job_description,
            'quality_level': quality_level,
            'component_scores': component_scores,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'top_skills': match_result.matched_skills[:10],
            'missing_skills': match_result.missing_skills[:8],
            'key_recommendations': match_result.recommendations[:5]
        }
    
    def _generate_executive_summary(self, data: Dict) -> str:
        """Generate executive summary for quick decision making"""
        
        template = f"""
EXECUTIVE SUMMARY - CANDIDATE ASSESSMENT
{'=' * 50}

Candidate: {data['candidate_name']}
Position: {data['job_title']}
Analysis Date: {data['analysis_date']}
Recruiter: {data['recruiter_name']}

OVERALL ASSESSMENT: {data['quality_level'][2]} ({data['match_result'].overall_score:.1f}%)

KEY FINDINGS:
• Overall match score of {data['match_result'].overall_score:.1f}% indicates {data['quality_level'][2].lower()}
• Strongest areas: {', '.join(data['strengths']) if data['strengths'] else 'None identified'}
• Areas for improvement: {', '.join(data['weaknesses']) if data['weaknesses'] else 'None identified'}
• Skills match: {len(data['top_skills'])} matched, {len(data['missing_skills'])} missing

RECOMMENDATION: {self._get_hiring_recommendation(data['match_result'].overall_score)}

NEXT STEPS:
{self._format_next_steps(data)}
        """
        
        return template.strip()
    
    def _format_next_steps(self, data: Dict) -> str:
        """Format next steps and recommendations for the candidate."""
        next_steps = []
        score = data['match_result'].overall_score
        
        if score >= 85:
            next_steps.append("• Schedule interview immediately - excellent candidate match")
            next_steps.append("• Prepare advanced technical assessment")
            next_steps.append("• Consider fast-track hiring process")
        elif score >= 70:
            next_steps.append("• Proceed to next interview round")
            next_steps.append("• Focus on validating top skills during interview")
            next_steps.append("• Prepare role-specific scenarios for discussion")
        elif score >= 55:
            next_steps.append("• Consider for next round with additional screening")
            next_steps.append("• Focus interview on gap areas identified")
            next_steps.append("• Assess potential for growth and learning")
        elif score >= 40:
            next_steps.append("• Review candidate's potential for growth carefully")
            next_steps.append("• Consider alternative roles that might be better fit")
            next_steps.append("• Extended evaluation period may be needed")
        else:
            next_steps.append("• Candidate may not be suitable for this specific role")
            next_steps.append("• Keep profile for future opportunities")
            next_steps.append("• Provide constructive feedback if possible")
        
        # Add specific recommendations based on key findings
        if data['key_recommendations']:
            next_steps.append("\nSpecific Action Items:")
            for i, rec in enumerate(data['key_recommendations'][:3], 1):
                next_steps.append(f"  {i}. {rec}")
        
        return "\n".join(next_steps)
    
    def _generate_detailed_analysis(self, data: Dict) -> str:
        """Generate detailed component-by-component analysis"""
        
        analysis = f"""
DETAILED CANDIDATE ANALYSIS REPORT
{'=' * 40}

CANDIDATE INFORMATION:
Name: {data['candidate_name']}
Position Applied: {data['job_title']}
Analysis Conducted: {data['analysis_date']} at {data['analysis_time']}
Analyzed by: {data['recruiter_name']}

OVERALL MATCH SCORE: {data['match_result'].overall_score:.1f}%
Quality Rating: {data['quality_level'][2]}

COMPONENT BREAKDOWN:
{'-' * 25}

1. SKILLS ANALYSIS ({data['match_result'].skills_score:.1f}%)
   {self._get_score_interpretation(data['match_result'].skills_score)}
   
   ✅ Matched Skills ({len(data['top_skills'])}):
   {self._format_list(data['top_skills'], '   • ')}
   
   ❌ Missing Skills ({len(data['missing_skills'])}):
   {self._format_list(data['missing_skills'], '   • ')}

2. EXPERIENCE ANALYSIS ({data['match_result'].experience_score:.1f}%)
   {self._get_score_interpretation(data['match_result'].experience_score)}
   
   Total Experience: {data['parsed_resume'].get('total_experience_years', 'Not specified')} years
   Experience Gap: {getattr(data['match_result'], 'experience_gap', 0):.1f} years
   
   Professional Background:
   {self._format_experience(data['parsed_resume'].get('experience', []))}

3. EDUCATION ANALYSIS ({data['match_result'].education_score:.1f}%)
   {self._get_score_interpretation(data['match_result'].education_score)}
   
   Educational Background:
   {self._format_education(data['parsed_resume'].get('education', []))}

4. KEYWORD RELEVANCE ({data['match_result'].keywords_score:.1f}%)
   {self._get_score_interpretation(data['match_result'].keywords_score)}
   
   Resume-to-job description alignment analysis shows 
   {self._get_keyword_assessment(data['match_result'].keywords_score)}

5. PROFESSIONAL SUMMARY ({data['match_result'].summary_score:.1f}%)
   {self._get_score_interpretation(data['match_result'].summary_score)}
   
   Candidate Summary: "{data['parsed_resume'].get('summary', 'No summary provided')[:200]}..."

CONTACT INFORMATION:
{self._format_contact_info(data['parsed_resume'].get('contact_info', {}))}
        """
        
        return analysis.strip()
    
    def _get_keyword_assessment(self, score: float) -> str:
        """Get keyword assessment based on score"""
        if score >= 75:
            return "strong alignment with job requirements and terminology"
        elif score >= 60:
            return "good alignment with some gaps in key terminology"
        elif score >= 45:
            return "moderate alignment with several terminology gaps"
        else:
            return "weak alignment requiring significant improvement"
    
    def _generate_hiring_recommendation(self, data: Dict) -> str:
        """Generate specific hiring recommendation with reasoning"""
        
        score = data['match_result'].overall_score
        recommendation = self._get_hiring_recommendation(score)
        
        report = f"""
HIRING RECOMMENDATION REPORT
{'=' * 30}

Candidate: {data['candidate_name']}
Position: {data['job_title']}
Date: {data['analysis_date']}

RECOMMENDATION: {recommendation}

REASONING:
{self._get_detailed_reasoning(data)}

RISK ASSESSMENT:
{self._assess_hiring_risks(data)}

DECISION FACTORS:
Positive Indicators:
{self._format_list(self._get_positive_indicators(data), '• ')}

Areas of Concern:
{self._format_list(self._get_concerns(data), '• ')}

COMPARATIVE ASSESSMENT:
This candidate scores in the {self._get_percentile_range(score)} percentile 
for this position type based on our analysis criteria.

FINAL RECOMMENDATION:
{self._get_final_recommendation(data)}
        """
        
        return report.strip()
    
    def _get_detailed_reasoning(self, data: Dict) -> str:
        """Generate detailed reasoning for hiring recommendation"""
        score = data['match_result'].overall_score
        
        if score >= 85:
            return f"Candidate demonstrates exceptional alignment with position requirements across all evaluation criteria. Strong skill match ({data['match_result'].skills_score:.1f}%) and relevant experience ({data['match_result'].experience_score:.1f}%) indicate high probability of success."
        elif score >= 70:
            return f"Candidate shows strong overall fit with minor gaps that can be addressed through training. Key strengths in {', '.join(data['strengths'][:2])} offset concerns in {', '.join(data['weaknesses'][:1]) if data['weaknesses'] else 'no major areas'}."
        elif score >= 55:
            return f"Candidate demonstrates potential but has notable gaps requiring careful consideration. Success would depend on additional training and support in {', '.join(data['weaknesses'][:2])}."
        else:
            return f"Candidate shows significant gaps across multiple criteria ({', '.join(data['weaknesses'])}) that would require extensive development to meet position requirements."
    
    def _assess_hiring_risks(self, data: Dict) -> str:
        """Assess hiring risks based on analysis"""
        risks = []
        score = data['match_result'].overall_score
        
        if score < 60:
            risks.append("• High onboarding and training investment required")
        if len(data['missing_skills']) > 3:
            risks.append("• Significant skill development needed")
        if data['match_result'].experience_score < 50:
            risks.append("• Limited relevant experience may impact immediate productivity")
        
        if not risks:
            risks.append("• Low risk hire with good probability of success")
        
        return "\n".join(risks)
    
    def _get_percentile_range(self, score: float) -> str:
        """Get percentile range description"""
        if score >= 85:
            return "top 15%"
        elif score >= 70:
            return "top 30%"
        elif score >= 55:
            return "middle 40%"
        else:
            return "bottom 30%"
    
    def _get_final_recommendation(self, data: Dict) -> str:
        """Generate final recommendation summary"""
        score = data['match_result'].overall_score
        
        if score >= 85:
            return "PROCEED WITH OFFER - Exceptional candidate who meets and exceeds requirements."
        elif score >= 70:
            return "PROCEED TO FINAL INTERVIEW - Strong candidate worth pursuing with standard process."
        elif score >= 55:
            return "PROCEED WITH CAUTION - Consider additional evaluation and specific development plan."
        else:
            return "EXPLORE ALTERNATIVES - Consider other candidates or alternative roles for this individual."
    
    def _generate_interview_guide(self, data: Dict) -> str:
        """Generate targeted interview questions and focus areas"""
        
        guide = f"""
INTERVIEW PREPARATION GUIDE
{'=' * 28}

Candidate: {data['candidate_name']}
Position: {data['job_title']}
Prepared for: {data['recruiter_name']}

INTERVIEW FOCUS AREAS:
{'-' * 22}

HIGH-PRIORITY DISCUSSION TOPICS:
{self._format_list(self._get_interview_priorities(data), '1. ', numbered=True)}

TECHNICAL ASSESSMENT AREAS:
Skills to Validate:
{self._format_list(data['top_skills'][:5], '• ')}

Skills Gaps to Explore:
{self._format_list(data['missing_skills'][:3], '• ')}

SUGGESTED INTERVIEW QUESTIONS:

Technical Questions:
{self._generate_technical_questions(data)}

Experience-Based Questions:
{self._generate_experience_questions(data)}

Cultural Fit Questions:
{self._generate_culture_questions(data)}

RED FLAGS TO WATCH FOR:
{self._format_list(self._get_red_flags(data), '⚠ ')}

POSITIVE INDICATORS TO CONFIRM:
{self._format_list(self._get_positive_indicators(data), '✅ ')}
        """
        
        return guide.strip()
    
    def _generate_candidate_feedback(self, data: Dict) -> str:
        """Generate constructive feedback report for candidates"""
        
        feedback = f"""
CANDIDATE DEVELOPMENT FEEDBACK
{'=' * 30}

Dear {data['candidate_name']},

Thank you for your interest in the {data['job_title']} position. 
We have completed a comprehensive analysis of your application.

OVERALL ASSESSMENT:
Your application received a match score of {data['match_result'].overall_score:.1f}%, 
indicating {data['quality_level'][2].lower()} alignment with our requirements.

STRENGTHS IDENTIFIED:
{self._format_list(self._get_candidate_strengths(data), '✅ ')}

DEVELOPMENT OPPORTUNITIES:
{self._format_list(data['key_recommendations'], '💡 ')}

SPECIFIC SKILL RECOMMENDATIONS:
Technical Skills to Develop:
{self._format_list(data['missing_skills'][:5], '• ')}

NEXT STEPS FOR PROFESSIONAL GROWTH:
{self._format_development_plan(data)}

We encourage you to continue developing your professional profile 
and consider reapplying for future opportunities that align with your growth.

Best regards,
{data['recruiter_name']}
Talent Acquisition Team
        """
        
        return feedback.strip()
    
    def _get_candidate_strengths(self, data: Dict) -> List[str]:
        """Identify candidate strengths for feedback"""
        strengths = []
        
        if data['match_result'].skills_score > 70:
            strengths.append("Strong technical skill portfolio")
        if data['match_result'].experience_score > 70:
            strengths.append("Relevant professional experience")
        if data['match_result'].education_score > 70:
            strengths.append("Strong educational background")
        if len(data['top_skills']) > 5:
            strengths.append("Diverse skill set with good breadth")
        
        return strengths or ["Professional application and documentation"]
    
    def _format_development_plan(self, data: Dict) -> str:
        """Format development plan for candidates"""
        plan = []
        
        if data['missing_skills']:
            plan.append(f"• Focus on developing: {', '.join(data['missing_skills'][:3])}")
        
        if data['match_result'].experience_score < 60:
            plan.append("• Seek opportunities to gain more relevant experience")
        
        plan.append("• Continue building your professional network")
        plan.append("• Consider additional certifications in your field")
        
        return "\n".join(plan)
    
    def _generate_full_report(self, reports: Dict, data: Dict) -> str:
        """Combine all reports into comprehensive document"""
        
        full_report = f"""
COMPREHENSIVE CANDIDATE ANALYSIS REPORT
{'=' * 45}

Generated: {data['analysis_date']} at {data['analysis_time']}
Report ID: {self._generate_report_id(data)}

{reports['executive_summary']}

{'=' * 60}

{reports['detailed_analysis']}

{'=' * 60}

{reports['hiring_recommendation']}

{'=' * 60}

{reports['interview_guide']}

{'=' * 60}
END OF REPORT
        """
        
        return full_report.strip()
    
    def _load_templates(self) -> Dict:
        """Load report templates (placeholder for future template system)"""
        return {
            'executive': "Executive Summary Template",
            'detailed': "Detailed Analysis Template", 
            'recommendation': "Hiring Recommendation Template"
        }
    
    def _get_quality_level(self, score: float) -> Tuple[int, int, str]:
        """Determine quality level based on score"""
        for level, (min_score, max_score, description) in self.quality_levels.items():
            if min_score <= score <= max_score:
                return (min_score, max_score, description)
        return (0, 39, "Poor Match")
    
    def _get_score_interpretation(self, score: float) -> str:
        """Get textual interpretation of component score"""
        if score >= 85:
            return "Excellent performance in this area."
        elif score >= 70:
            return "Strong performance with minor gaps."
        elif score >= 55:
            return "Moderate performance with room for improvement."
        elif score >= 40:
            return "Below expectations with significant gaps."
        else:
            return "Critical deficiencies requiring attention."
    
    def _get_hiring_recommendation(self, score: float) -> str:
        """Get hiring recommendation based on overall score"""
        if score >= 85:
            return "STRONG HIRE - Excellent candidate match"
        elif score >= 70:
            return "HIRE - Good candidate with minor gaps"
        elif score >= 55:
            return "CONDITIONAL HIRE - Consider with reservations"
        elif score >= 40:
            return "WEAK CANDIDATE - High risk hire"
        else:
            return "DO NOT HIRE - Poor fit for position"
    
    def _format_list(self, items: List[str], prefix: str = '• ', numbered: bool = False) -> str:
        """Format list items with consistent styling"""
        if not items:
            return f"{prefix}None identified"
        
        if numbered:
            return '\n'.join([f"{i}. {item}" for i, item in enumerate(items, 1)])
        else:
            return '\n'.join([f"{prefix}{item}" for item in items])
    
    def _format_experience(self, experience: List[Dict]) -> str:
        """Format experience information"""
        if not experience:
            return "   • No experience information available"
        
        formatted = []
        for exp in experience[:3]:
            title = exp.get('title', 'Position not specified')
            context = exp.get('context', '')[:100] + "..." if len(exp.get('context', '')) > 100 else exp.get('context', '')
            formatted.append(f"   • {title}\n     {context}")
        
        return '\n'.join(formatted)
    
    def _format_education(self, education: List[Dict]) -> str:
        """Format education information"""
        if not education:
            return "   • No education information available"
        
        formatted = []
        for edu in education[:2]:
            institution = edu.get('institution', 'Institution not specified')
            formatted.append(f"   • {institution}")
        
        return '\n'.join(formatted)
    
    def _format_contact_info(self, contact_info: Dict) -> str:
        """Format contact information"""
        formatted = []
        if contact_info.get('email'):
            formatted.append(f"Email: {contact_info['email']}")
        if contact_info.get('phone'):
            formatted.append(f"Phone: {contact_info['phone']}")
        if contact_info.get('linkedin'):
            formatted.append(f"LinkedIn: {contact_info['linkedin']}")
        
        return '\n'.join(formatted) if formatted else "Contact information not available"
    
    def _generate_report_id(self, data: Dict) -> str:
        """Generate unique report ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        candidate_id = data['candidate_name'].replace(' ', '_').upper()
        return f"RPT_{candidate_id}_{timestamp}"
    
    def _get_interview_priorities(self, data: Dict) -> List[str]:
        """Generate priority interview topics"""
        priorities = []
        
        if data['match_result'].experience_score < 60:
            priorities.append("Validate claimed experience and responsibilities")
        
        if len(data['missing_skills']) > 3:
            priorities.append("Assess learning agility and skill acquisition")
        
        if data['match_result'].skills_score > 80:
            priorities.append("Deep dive into technical expertise")
        
        priorities.append("Cultural fit and team collaboration")
        priorities.append("Career goals and motivation")
        
        return priorities[:5]
    
    def _generate_technical_questions(self, data: Dict) -> str:
        """Generate relevant technical questions"""
        questions = []
        
        for skill in data['top_skills'][:3]:
            questions.append(f"• Describe a challenging project where you used {skill}")
        
        for skill in data['missing_skills'][:2]:
            questions.append(f"• How would you approach learning {skill}?")
        
        return '\n'.join(questions)
    
    def _generate_experience_questions(self, data: Dict) -> str:
        """Generate experience-based questions"""
        return """• Walk me through your most significant professional achievement
• Describe a time when you had to learn new technology quickly
• How do you handle working under pressure or tight deadlines?
• Tell me about a project that didn't go as planned"""
    
    def _generate_culture_questions(self, data: Dict) -> str:
        """Generate culture fit questions"""
        return """• What type of work environment brings out your best performance?
• How do you prefer to receive feedback and recognition?
• Describe your ideal team collaboration style
• What motivates you most in your professional work?"""
    
    def _get_red_flags(self, data: Dict) -> List[str]:
        """Identify potential red flags"""
        flags = []
        
        if data['match_result'].overall_score < 40:
            flags.append("Very low overall match score")
        
        if len(data['missing_skills']) > 5:
            flags.append("Significant skill gaps")
        
        if data['match_result'].experience_score < 30:
            flags.append("Insufficient relevant experience")
        
        return flags or ["No major red flags identified"]
    
    def _get_positive_indicators(self, data: Dict) -> List[str]:
        """Identify positive indicators"""
        indicators = []
        
        if data['match_result'].skills_score > 75:
            indicators.append("Strong technical skill match")
        
        if data['match_result'].experience_score > 70:
            indicators.append("Relevant experience level")
        
        if len(data['strengths']) > 2:
            indicators.append("Multiple areas of strength")
        
        return indicators or ["Review individual components"]
    
    def _get_concerns(self, data: Dict) -> List[str]:
        """Identify areas of concern"""
        concerns = []
        
        for weakness in data['weaknesses']:
            concerns.append(f"Below average {weakness.lower()} score")
        
        if hasattr(data['match_result'], 'experience_gap') and data['match_result'].experience_gap > 2:
            concerns.append(f"Experience gap of {data['match_result'].experience_gap:.1f} years")
        
        return concerns or ["No significant concerns identified"]

    def export_to_file(self, report_content: str, filename: str, format_type: str = "txt") -> str:
        """Export report to file"""
        try:
            filepath = Path(f"{filename}.{format_type}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Report exported to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            return f"Export failed: {str(e)}"

# Production usage:
# generator = ReportGenerator()
# reports = generator.generate_comprehensive_report(match_result, parsed_resume, job_description, "John Doe", "Senior Developer")
# generator.export_to_file(reports['full_report'], "candidate_analysis_john_doe")