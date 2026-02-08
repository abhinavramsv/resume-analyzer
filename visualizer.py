import logging
from io import BytesIO
import base64
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeVisualizer:
    def __init__(self, theme: str = "plotly_white"):
        self.theme = theme
        self.color_scheme = {
            'excellent': '#2E8B57',
            'good': '#32CD32',
            'average': '#FFD700',
            'poor': '#FF6347',
            'critical': '#DC143C'
        }
        self.thresholds = {'excellent': 85, 'good': 70, 'average': 55, 'poor': 40}

    def create_comprehensive_dashboard(self, match_result, candidate_name: str = "Candidate", 
                                     job_title: str = "Position") -> Dict[str, str]:
        try:
            dashboard = {
                'gauge': self._create_score_gauge(match_result.overall_score, candidate_name, job_title),
                'radar': self._create_radar_chart(match_result, candidate_name),
                'skills_matrix': self._create_skills_matrix(match_result.matched_skills, match_result.missing_skills),
                'breakdown': self._create_score_breakdown(match_result),
                'recommendations': self._create_recommendations_visual(match_result.recommendations)
            }
            
            if hasattr(match_result, 'experience_gap'):
                dashboard['experience'] = self._create_experience_visualization(match_result)
                
            return dashboard
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return {'error': str(e)}

    def _create_score_gauge(self, score: float, name: str, title: str) -> str:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={'text': f"{name}<br>{title} Match"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': self._get_score_color(score)},
                'steps': [
                    {'range': [0, 50], 'color': "#eeeeee"},
                    {'range': [50, 75], 'color': "#dddddd"},
                    {'range': [75, 100], 'color': "#cccccc"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'value': 70}
            }
        ))
        fig.update_layout(height=350, margin=dict(t=50, b=10, l=10, r=10))
        return fig.to_html(include_plotlyjs='cdn', full_html=False)

    def _create_radar_chart(self, result, name: str) -> str:
        categories = ['Skills', 'Experience', 'Education', 'Keywords', 'Summary']
        scores = [result.skills_score, result.experience_score, result.education_score, 
                  result.keywords_score, result.summary_score]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name=name,
            line_color='#20c997'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
                          showlegend=False, title="Score Distribution", height=450)
        return fig.to_html(include_plotlyjs='cdn', full_html=False)

    def _create_skills_matrix(self, matched: List[str], missing: List[str]) -> str:
        data = []
        for s in matched[:8]: data.append({'Skill': s, 'Status': 'Matched', 'Val': 1})
        for s in missing[:8]: data.append({'Skill': s, 'Status': 'Missing', 'Val': 1})
        
        if not data: return "<div>No skills data</div>"
        
        df = pd.DataFrame(data)
        fig = px.bar(df, x='Skill', y='Val', color='Status',
                     color_discrete_map={'Matched': '#2E8B57', 'Missing': '#FF6347'},
                     title="Key Skills Check")
        fig.update_layout(height=350, showlegend=True, yaxis_visible=False)
        return fig.to_html(include_plotlyjs='cdn', full_html=False)

    def _create_score_breakdown(self, result) -> str:
        categories = ['Skills', 'Experience', 'Education', 'Keywords', 'Summary']
        scores = [result.skills_score, result.experience_score, result.education_score, 
                  result.keywords_score, result.summary_score]
        
        fig = go.Figure(go.Bar(
            x=scores, y=categories, orientation='h',
            marker_color=[self._get_score_color(s) for s in scores],
            text=[f"{s}%" for s in scores], textposition='auto'
        ))
        fig.update_layout(title="Metric Breakdown", xaxis=dict(range=[0, 100]), height=350)
        return fig.to_html(include_plotlyjs='cdn', full_html=False)

    def _create_experience_visualization(self, result) -> str:
        score = result.experience_score
        fig = go.Figure(go.Indicator(
            mode="number+gauge",
            value=score,
            title={'text': "Experience Score"},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#17a2b8"}}
        ))
        fig.update_layout(height=250)
        return fig.to_html(include_plotlyjs='cdn', full_html=False)

    def _create_recommendations_visual(self, recs: List[str]) -> str:
        if not recs: return "<div style='color:green'>No critical gaps identified.</div>"
        items = "".join([f"<li style='margin-bottom:8px'><b>{i+1}.</b> {r}</li>" for i, r in enumerate(recs[:4])])
        return f"""
        <div style="font-family:sans-serif; border:1px solid #ddd; padding:15px; border-radius:8px">
            <h4 style="margin-top:0">💡 Quick Fixes</h4>
            <ul style="padding-left:20px">{items}</ul>
        </div>
        """

    def _get_score_color(self, score: float) -> str:
        if score >= 85: return self.color_scheme['excellent']
        if score >= 70: return self.color_scheme['good']
        if score >= 55: return self.color_scheme['average']
        return self.color_scheme['poor']

    def export_dashboard_html(self, dashboard: Dict[str, str], name: str, title: str) -> str:
        return f"""
        <html>
        <head><title>Report: {name}</title></head>
        <body style="font-family:sans-serif; background:#f4f7f6; padding:20px">
            <div style="max-width:1000px; margin:auto; background:white; padding:30px; border-radius:12px; shadow:0 4px 6px rgba(0,0,0,0.1)">
                <h1>Resume Analysis - {name}</h1>
                <h3>Target: {title}</h3>
                <hr>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px">
                    <div>{dashboard.get('gauge', '')}</div>
                    <div>{dashboard.get('radar', '')}</div>
                </div>
                <div style="margin-top:20px">{dashboard.get('breakdown', '')}</div>
                <div style="margin-top:20px">{dashboard.get('skills_matrix', '')}</div>
                <div style="margin-top:20px">{dashboard.get('recommendations', '')}</div>
            </div>
        </body>
        </html>
        """
