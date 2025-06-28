"""
Resume Visualizer Module
Creates interactive charts and visual representations of resume match scores
"""

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from io import BytesIO
import base64
from dataclasses import asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set styling
plt.style.use('default')
sns.set_palette("husl")

class ResumeVisualizer:
    """
    Creates comprehensive visualizations for resume matching results
    """
    
    def __init__(self, theme: str = "plotly_white"):
        self.theme = theme
        self.color_scheme = {
            'excellent': '#2E8B57',    # Sea Green
            'good': '#32CD32',         # Lime Green  
            'average': '#FFD700',      # Gold
            'poor': '#FF6347',         # Tomato
            'critical': '#DC143C'      # Crimson
        }
        
        # Score thresholds
        self.thresholds = {
            'excellent': 85,
            'good': 70,
            'average': 55,
            'poor': 40
        }
    
    def create_comprehensive_dashboard(self, match_result, candidate_name: str = "Candidate", 
                                    job_title: str = "Position") -> Dict[str, str]:
        """
        Create a comprehensive dashboard with multiple visualizations
        
        Args:
            match_result: MatchResult object from scoring.py
            candidate_name: Name of the candidate
            job_title: Job position title
            
        Returns:
            Dictionary with base64 encoded images and HTML content
        """
        try:
            dashboard = {}
            
            # 1. Overall Score Gauge
            dashboard['gauge'] = self._create_score_gauge(
                match_result.overall_score, candidate_name, job_title
            )
            
            # 2. Component Breakdown Radar Chart
            dashboard['radar'] = self._create_radar_chart(match_result, candidate_name)
            
            # 3. Skills Match Matrix
            dashboard['skills_matrix'] = self._create_skills_matrix(
                match_result.matched_skills, match_result.missing_skills
            )
            
            # 4. Score Breakdown Bar Chart
            dashboard['breakdown'] = self._create_score_breakdown(match_result)
            
            # 5. Experience Timeline (if data available)
            if hasattr(match_result, 'experience_gap'):
                dashboard['experience'] = self._create_experience_visualization(match_result)
            
            # 6. Recommendations Panel
            dashboard['recommendations'] = self._create_recommendations_visual(
                match_result.recommendations
            )
            
            # 7. Comparative Score Distribution
            dashboard['distribution'] = self._create_score_distribution(match_result)
            
            logger.info(f"Dashboard created successfully for {candidate_name}")
            return dashboard
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return {'error': f"Visualization error: {str(e)}"}
    
    def _create_score_gauge(self, overall_score: float, candidate_name: str, 
                          job_title: str) -> str:
        """Create an interactive gauge chart for overall score"""
        
        # Determine score category and color
        color = self._get_score_color(overall_score)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = overall_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"{candidate_name}<br>Match Score for {job_title}"},
            delta = {'reference': 70, 'increasing': {'color': "green"}, 
                    'decreasing': {'color': "red"}},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 55], 'color': "lightyellow"},
                    {'range': [55, 70], 'color': "lightgreen"},
                    {'range': [70, 85], 'color': "green"},
                    {'range': [85, 100], 'color': "darkgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor="white",
            font={'color': "darkblue", 'family': "Arial"},
            title_font_size=16,
            height=400
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="gauge_chart")
    
    def _create_radar_chart(self, match_result, candidate_name: str) -> str:
        """Create radar chart showing component scores"""
        
        categories = ['Skills', 'Experience', 'Education', 'Keywords', 'Summary']
        scores = [
            match_result.skills_score,
            match_result.experience_score, 
            match_result.education_score,
            match_result.keywords_score,
            match_result.summary_score
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],  # Close the polygon
            theta=categories + [categories[0]],
            fill='toself',
            name=candidate_name,
            line_color='rgb(32, 201, 151)',
            fillcolor='rgba(32, 201, 151, 0.3)'
        ))
        
        # Add benchmark line at 70%
        benchmark_scores = [70] * len(categories)
        fig.add_trace(go.Scatterpolar(
            r=benchmark_scores + [benchmark_scores[0]],
            theta=categories + [categories[0]],
            fill='none',
            name='Benchmark (70%)',
            line=dict(color='red', dash='dash', width=2)
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    ticksuffix='%'
                )
            ),
            showlegend=True,
            title=f"Component Score Breakdown - {candidate_name}",
            title_x=0.5,
            height=500
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="radar_chart")
    
    def _create_skills_matrix(self, matched_skills: List[str], 
                            missing_skills: List[str]) -> str:
        """Create visual matrix of matched vs missing skills"""
        
        # Prepare data
        all_skills = matched_skills + missing_skills
        if not all_skills:
            return "<div>No skills data available</div>"
        
        # Limit to top 15 skills for readability
        matched_display = matched_skills[:10]
        missing_display = missing_skills[:10]
        
        skills_data = []
        for skill in matched_display:
            skills_data.append({'Skill': skill, 'Status': 'Matched', 'Value': 1})
        for skill in missing_display:
            skills_data.append({'Skill': skill, 'Status': 'Missing', 'Value': 1})
        
        if not skills_data:
            return "<div>No skills to display</div>"
        
        df = pd.DataFrame(skills_data)
        
        # Create heatmap-style visualization
        fig = px.bar(df, x='Skill', y='Value', color='Status',
                    color_discrete_map={'Matched': '#2E8B57', 'Missing': '#FF6347'},
                    title="Skills Match Analysis",
                    labels={'Value': 'Skill Status'})
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400,
            showlegend=True,
            title_x=0.5
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="skills_matrix")
    
    def _create_score_breakdown(self, match_result) -> str:
        """Create horizontal bar chart for score breakdown"""
        
        categories = ['Skills', 'Experience', 'Education', 'Keywords', 'Summary']
        scores = [
            match_result.skills_score,
            match_result.experience_score,
            match_result.education_score, 
            match_result.keywords_score,
            match_result.summary_score
        ]
        
        colors = [self._get_score_color(score) for score in scores]
        
        fig = go.Figure(go.Bar(
            x=scores,
            y=categories,
            orientation='h',
            marker_color=colors,
            text=[f"{score:.1f}%" for score in scores],
            textposition='inside',
            textfont=dict(color='white', size=12)
        ))
        
        fig.update_layout(
            title="Detailed Score Breakdown",
            xaxis_title="Score (%)",
            yaxis_title="Categories",
            height=400,
            title_x=0.5,
            xaxis=dict(range=[0, 100])
        )
        
        # Add benchmark line
        fig.add_vline(x=70, line_dash="dash", line_color="red", 
                     annotation_text="Target (70%)")
        
        return fig.to_html(include_plotlyjs='cdn', div_id="breakdown_chart")
    
    def _create_experience_visualization(self, match_result) -> str:
        """Create experience gap visualization"""
        
        if not hasattr(match_result, 'experience_gap'):
            return "<div>Experience data not available</div>"
        
        experience_gap = getattr(match_result, 'experience_gap', 0)
        current_score = match_result.experience_score
        
        # Create a simple progress bar style visualization
        fig = go.Figure()
        
        # Current experience level
        fig.add_trace(go.Bar(
            x=['Experience Match'],
            y=[current_score],
            name='Current Level',
            marker_color=self._get_score_color(current_score),
            text=f"{current_score:.1f}%",
            textposition='inside'
        ))
        
        # Target level
        fig.add_trace(go.Bar(
            x=['Experience Match'],
            y=[100 - current_score],
            name='Gap to Excellence',
            marker_color='lightgray',
            base=current_score,
            showlegend=False
        ))
        
        fig.update_layout(
            title=f"Experience Analysis (Gap: {experience_gap:.1f} years)",
            yaxis_title="Score (%)",
            height=300,
            title_x=0.5,
            barmode='stack',
            yaxis=dict(range=[0, 100])
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="experience_chart")
    
    def _create_recommendations_visual(self, recommendations: List[str]) -> str:
        """Create visual representation of recommendations"""
        
        if not recommendations:
            return "<div class='alert alert-success'>No improvement areas identified - excellent candidate!</div>"
        
        html_content = """
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0;">
            <h4 style="color: #495057; margin-bottom: 15px;">🎯 Recommendations for Improvement</h4>
            <ul style="list-style-type: none; padding-left: 0;">
        """
        
        for i, rec in enumerate(recommendations[:5], 1):
            icon = "🔍" if "gap" in rec.lower() else "💡"
            html_content += f"""
                <li style="margin-bottom: 10px; padding: 10px; background-color: white; 
                           border-radius: 5px; border-left: 4px solid #007bff;">
                    <strong>{icon} {i}.</strong> {rec}
                </li>
            """
        
        html_content += """
            </ul>
        </div>
        """
        
        return html_content
    
    def _create_score_distribution(self, match_result) -> str:
        """Create distribution chart showing how candidate performs across categories"""
        
        scores = [
            match_result.skills_score,
            match_result.experience_score,
            match_result.education_score,
            match_result.keywords_score, 
            match_result.summary_score
        ]
        
        # Create histogram of scores
        fig = go.Figure(data=[go.Histogram(
            x=scores,
            nbinsx=5,
            marker_color='rgba(50, 171, 96, 0.7)',
            name='Score Distribution'
        )])
        
        fig.update_layout(
            title="Score Distribution Across Categories",
            xaxis_title="Score Range (%)",
            yaxis_title="Number of Categories",
            height=300,
            title_x=0.5
        )
        
        # Add overall score line
        fig.add_vline(x=match_result.overall_score, line_dash="dash", 
                     line_color="red", annotation_text=f"Overall: {match_result.overall_score:.1f}%")
        
        return fig.to_html(include_plotlyjs='cdn', div_id="distribution_chart")
    
    def _get_score_color(self, score: float) -> str:
        """Get color based on score value"""
        if score >= self.thresholds['excellent']:
            return self.color_scheme['excellent']
        elif score >= self.thresholds['good']:
            return self.color_scheme['good']
        elif score >= self.thresholds['average']:
            return self.color_scheme['average']
        elif score >= self.thresholds['poor']:
            return self.color_scheme['poor']
        else:
            return self.color_scheme['critical']
    
    def create_comparison_chart(self, candidates_results: List[Tuple[str, any]]) -> str:
        """
        Create comparison chart for multiple candidates
        
        Args:
            candidates_results: List of tuples (candidate_name, match_result)
        """
        if len(candidates_results) < 2:
            return "<div>Need at least 2 candidates for comparison</div>"
        
        # Prepare data for comparison
        comparison_data = []
        for name, result in candidates_results[:10]:  # Limit to top 10
            comparison_data.append({
                'Candidate': name,
                'Overall': result.overall_score,
                'Skills': result.skills_score,
                'Experience': result.experience_score,
                'Education': result.education_score,
                'Keywords': result.keywords_score,
                'Summary': result.summary_score
            })
        
        df = pd.DataFrame(comparison_data)
        
        # Create grouped bar chart
        fig = go.Figure()
        
        categories = ['Skills', 'Experience', 'Education', 'Keywords', 'Summary']
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, category in enumerate(categories):
            fig.add_trace(go.Bar(
                name=category,
                x=df['Candidate'],
                y=df[category],
                marker_color=colors[i]
            ))
        
        fig.update_layout(
            title="Candidate Comparison - Component Scores",
            xaxis_title="Candidates", 
            yaxis_title="Score (%)",
            barmode='group',
            height=500,
            title_x=0.5,
            xaxis_tickangle=-45
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="comparison_chart")
    
    def export_dashboard_html(self, dashboard: Dict[str, str], 
                            candidate_name: str, job_title: str) -> str:
        """
        Export complete dashboard as standalone HTML file
        """
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Resume Analysis Dashboard - {candidate_name}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ text-align: center; background-color: white; padding: 20px; 
                          border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .chart-container {{ background-color: white; padding: 20px; margin-bottom: 20px; 
                                   border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .row {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                .col-6 {{ flex: 1; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Resume Analysis Dashboard</h1>
                    <h2>{candidate_name} - {job_title}</h2>
                    <p>Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="row">
                    <div class="col-6">
                        <div class="chart-container">
                            {dashboard.get('gauge', '')}
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="chart-container">
                            {dashboard.get('radar', '')}
                        </div>
                    </div>
                </div>
                
                <div class="chart-container">
                    {dashboard.get('breakdown', '')}
                </div>
                
                <div class="row">
                    <div class="col-6">
                        <div class="chart-container">
                            {dashboard.get('skills_matrix', '')}
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="chart-container">
                            {dashboard.get('experience', '')}
                        </div>
                    </div>
                </div>
                
                <div class="chart-container">
                    {dashboard.get('recommendations', '')}
                </div>
                
            </div>
        </body>
        </html>
        """
        
        return html_template

# Production usage:
# visualizer = ResumeVisualizer()
# dashboard = visualizer.create_comprehensive_dashboard(match_result, "John Doe", "Senior Developer")
# html_output = visualizer.export_dashboard_html(dashboard, "John Doe", "Senior Developer")