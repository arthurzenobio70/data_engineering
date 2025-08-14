#!/usr/bin/env python3
"""
Data Quality Dashboard
Generates monitoring dashboard for data quality metrics and test results.
"""

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from snowflake.connector import connect
import streamlit as st
import os

class DataQualityDashboard:
    """Data quality monitoring dashboard using Streamlit and Plotly."""
    
    def __init__(self):
        self.snowflake_config = {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'FINANCE_WH'),
            'database': os.getenv('SNOWFLAKE_DATABASE', 'FINANCE_DB'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA', 'TEST_FAILURES'),
        }
    
    def get_connection(self):
        """Get Snowflake connection."""
        return connect(**self.snowflake_config)
    
    def get_test_results(self, days=30):
        """Get test results from the last N days."""
        query = f"""
        SELECT 
            test_name,
            model_name,
            test_status,
            executed_at,
            error_message,
            rows_affected
        FROM test_results 
        WHERE executed_at >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
        ORDER BY executed_at DESC
        """
        
        with self.get_connection() as conn:
            return pd.read_sql(query, conn)
    
    def get_model_freshness(self):
        """Get model freshness information."""
        query = """
        SELECT 
            model_name,
            last_updated,
            DATEDIFF('hour', last_updated, CURRENT_TIMESTAMP()) as hours_since_update,
            row_count,
            freshness_status
        FROM model_freshness_summary
        ORDER BY hours_since_update DESC
        """
        
        with self.get_connection() as conn:
            return pd.read_sql(query, conn)
    
    def get_data_quality_metrics(self):
        """Get aggregated data quality metrics."""
        query = """
        SELECT 
            DATE(executed_at) as test_date,
            COUNT(*) as total_tests,
            SUM(CASE WHEN test_status = 'pass' THEN 1 ELSE 0 END) as passed_tests,
            SUM(CASE WHEN test_status = 'fail' THEN 1 ELSE 0 END) as failed_tests,
            ROUND(passed_tests::FLOAT / total_tests::FLOAT * 100, 2) as pass_rate
        FROM test_results 
        WHERE executed_at >= DATEADD(day, -30, CURRENT_TIMESTAMP())
        GROUP BY DATE(executed_at)
        ORDER BY test_date
        """
        
        with self.get_connection() as conn:
            return pd.read_sql(query, conn)
    
    def create_test_results_chart(self, df):
        """Create test results trend chart."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Daily Test Results', 'Test Pass Rate'),
            vertical_spacing=0.15
        )
        
        # Daily test counts
        fig.add_trace(
            go.Scatter(
                x=df['test_date'],
                y=df['passed_tests'],
                name='Passed',
                line=dict(color='green'),
                fill='tonexty'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['test_date'],
                y=df['failed_tests'],
                name='Failed',
                line=dict(color='red'),
                fill='tozeroy'
            ),
            row=1, col=1
        )
        
        # Pass rate
        fig.add_trace(
            go.Scatter(
                x=df['test_date'],
                y=df['pass_rate'],
                name='Pass Rate %',
                line=dict(color='blue', width=3),
                mode='lines+markers'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="Data Quality Test Results (Last 30 Days)",
            height=600,
            showlegend=True
        )
        
        return fig
    
    def create_freshness_chart(self, df):
        """Create data freshness monitoring chart."""
        # Color code based on freshness
        colors = []
        for hours in df['hours_since_update']:
            if hours <= 24:
                colors.append('green')
            elif hours <= 48:
                colors.append('orange')
            else:
                colors.append('red')
        
        fig = go.Figure(data=go.Bar(
            x=df['model_name'],
            y=df['hours_since_update'],
            marker_color=colors,
            text=df['hours_since_update'],
            textposition='auto',
        ))
        
        fig.update_layout(
            title="Model Freshness (Hours Since Last Update)",
            xaxis_title="Model Name",
            yaxis_title="Hours Since Update",
            height=400
        )
        
        # Add reference lines
        fig.add_hline(y=24, line_dash="dash", line_color="orange", 
                     annotation_text="24h Warning")
        fig.add_hline(y=48, line_dash="dash", line_color="red", 
                     annotation_text="48h Critical")
        
        return fig
    
    def create_test_failure_breakdown(self, df):
        """Create test failure breakdown by category."""
        failed_tests = df[df['test_status'] == 'fail']
        
        if failed_tests.empty:
            return go.Figure().add_annotation(
                text="No test failures in the selected period",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        # Group by test type (extract from test_name)
        failed_tests['test_type'] = failed_tests['test_name'].str.extract(r'(\w+)_test')[0]
        test_type_counts = failed_tests['test_type'].value_counts()
        
        fig = go.Figure(data=go.Pie(
            labels=test_type_counts.index,
            values=test_type_counts.values,
            hole=0.4
        ))
        
        fig.update_layout(
            title="Test Failures by Category",
            height=400
        )
        
        return fig
    
    def run_dashboard(self):
        """Run the Streamlit dashboard."""
        st.set_page_config(
            page_title="Data Quality Dashboard",
            page_icon="📊",
            layout="wide"
        )
        
        st.title("📊 Finance Data Platform - Quality Dashboard")
        st.markdown("Real-time monitoring of data quality metrics and test results")
        
        # Sidebar controls
        st.sidebar.header("Dashboard Controls")
        days_to_show = st.sidebar.slider("Days to show", 7, 90, 30)
        auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", False)
        
        if auto_refresh:
            st.sidebar.info("Dashboard will refresh every 60 seconds")
            # Auto-refresh placeholder
            placeholder = st.empty()
        
        try:
            # Load data
            with st.spinner("Loading data quality metrics..."):
                test_results = self.get_test_results(days_to_show)
                freshness_data = self.get_model_freshness()
                quality_metrics = self.get_data_quality_metrics()
            
            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            if not quality_metrics.empty:
                latest_metrics = quality_metrics.iloc[-1]
                
                with col1:
                    st.metric(
                        "Latest Pass Rate", 
                        f"{latest_metrics['pass_rate']:.1f}%",
                        delta=None
                    )
                
                with col2:
                    st.metric(
                        "Tests Today", 
                        int(latest_metrics['total_tests']),
                        delta=None
                    )
                
                with col3:
                    failed_today = int(latest_metrics['failed_tests'])
                    st.metric(
                        "Failed Tests", 
                        failed_today,
                        delta=f"-{failed_today}" if failed_today > 0 else "0"
                    )
                
                with col4:
                    stale_models = len(freshness_data[freshness_data['hours_since_update'] > 48])
                    st.metric(
                        "Stale Models", 
                        stale_models,
                        delta=f"-{stale_models}" if stale_models > 0 else "0"
                    )
            
            # Charts row
            col1, col2 = st.columns(2)
            
            with col1:
                if not quality_metrics.empty:
                    chart1 = self.create_test_results_chart(quality_metrics)
                    st.plotly_chart(chart1, use_container_width=True)
                else:
                    st.warning("No test metrics data available")
            
            with col2:
                if not test_results.empty:
                    chart2 = self.create_test_failure_breakdown(test_results)
                    st.plotly_chart(chart2, use_container_width=True)
                else:
                    st.warning("No test results data available")
            
            # Freshness chart
            if not freshness_data.empty:
                chart3 = self.create_freshness_chart(freshness_data)
                st.plotly_chart(chart3, use_container_width=True)
            else:
                st.warning("No freshness data available")
            
            # Detailed tables
            st.header("Detailed Views")
            
            tab1, tab2, tab3 = st.tabs(["Recent Test Failures", "Model Freshness", "All Test Results"])
            
            with tab1:
                failed_tests = test_results[test_results['test_status'] == 'fail'].head(20)
                if not failed_tests.empty:
                    st.dataframe(failed_tests, use_container_width=True)
                else:
                    st.success("No recent test failures! 🎉")
            
            with tab2:
                st.dataframe(freshness_data, use_container_width=True)
            
            with tab3:
                st.dataframe(test_results.head(100), use_container_width=True)
            
            # Footer
            st.markdown("---")
            st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")
            st.info("Please check your Snowflake connection settings.")

if __name__ == "__main__":
    dashboard = DataQualityDashboard()
    dashboard.run_dashboard()
