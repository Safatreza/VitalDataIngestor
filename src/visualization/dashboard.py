import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from src.data.vital_signs import VitalDataIngestor, VitalSigns
from src.analysis.baseline_comparator import Alert
from src.analysis.anomaly_detector import AnomalyPrediction

class VitalSignsDashboard:
    """Dashboard for visualizing patient vital signs."""
    
    def __init__(self):
        """Initialize the dashboard."""
        self.ingestor = VitalDataIngestor()
        
        # Set page config
        st.set_page_config(
            page_title="Patient Vital Signs Dashboard",
            page_icon="🏥",
            layout="wide"
        )
    
    def _create_vital_signs_chart(self, df: pd.DataFrame, vital_sign: str, title: str) -> go.Figure:
        """Create a line chart for a vital sign."""
        fig = go.Figure()
        
        # Add main line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df[vital_sign],
            mode='lines',
            name='Value',
            line=dict(color='blue')
        ))
        
        # Add baseline ranges if available
        if 'baseline_min' in df.columns and 'baseline_max' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['baseline_min'],
                mode='lines',
                name='Min Range',
                line=dict(color='green', dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['baseline_max'],
                mode='lines',
                name='Max Range',
                line=dict(color='red', dash='dash'),
                fill='tonexty'
            ))
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title='Time',
            yaxis_title=title,
            hovermode='x unified',
            showlegend=True
        )
        
        return fig
    
    def _create_alerts_table(self, alerts: List[Alert]) -> pd.DataFrame:
        """Create a table of alerts."""
        if not alerts:
            return pd.DataFrame()
        
        data = []
        for alert in alerts:
            data.append({
                'Vital Sign': alert.vital_sign,
                'Message': alert.message,
                'Severity': alert.severity.value,
                'Value': alert.value,
                'Normal Range': f"{alert.baseline_min:.1f} - {alert.baseline_max:.1f}"
            })
        
        return pd.DataFrame(data)
    
    def _create_anomaly_section(self, prediction: Optional[AnomalyPrediction]) -> None:
        """Create a section for anomaly predictions."""
        if prediction is None:
            return
        
        st.subheader("Anomaly Detection")
        
        # Create confidence gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prediction.confidence * 100,
            title={'text': "Anomaly Confidence"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "red" if prediction.is_anomaly else "green"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 100], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        
        fig.update_layout(height=200)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display individual vital sign scores
        if prediction.details:
            st.write("Individual Vital Sign Anomaly Scores:")
            scores_df = pd.DataFrame({
                'Vital Sign': list(prediction.details.keys()),
                'Anomaly Score': list(prediction.details.values())
            })
            st.bar_chart(scores_df.set_index('Vital Sign'))
    
    def run(self):
        """Run the dashboard."""
        st.title("Patient Vital Signs Dashboard")
        
        # Sidebar controls
        st.sidebar.header("Controls")
        
        # Patient selection (mock data for now)
        patient_id = st.sidebar.selectbox(
            "Select Patient",
            options=["P001", "P002", "P003"],
            index=0
        )
        
        # Time range selection
        time_range = st.sidebar.selectbox(
            "Select Time Range",
            options=["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last Week"],
            index=1
        )
        
        # Convert time range to timedelta
        time_delta = {
            "Last Hour": timedelta(hours=1),
            "Last 6 Hours": timedelta(hours=6),
            "Last 24 Hours": timedelta(hours=24),
            "Last Week": timedelta(weeks=1)
        }[time_range]
        
        # Get data
        start_time = datetime.now() - time_delta
        vital_signs_history = self.ingestor.get_vital_signs_history()
        
        # Filter data by time range
        filtered_data = [
            vs for vs in vital_signs_history
            if vs.timestamp >= start_time
        ]
        
        if not filtered_data:
            st.warning("No data available for the selected time range.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': vs.timestamp,
                'heart_rate': vs.heart_rate,
                'temperature': vs.temperature,
                'spo2': vs.spo2,
                'respiratory_rate': vs.respiratory_rate,
                'systolic_bp': vs.systolic_bp,
                'diastolic_bp': vs.diastolic_bp
            }
            for vs in filtered_data
        ])
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Vital Signs", "Alerts", "Analysis"])
        
        with tab1:
            st.header("Vital Signs Trends")
            
            # Create charts for each vital sign
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(
                    self._create_vital_signs_chart(df, 'heart_rate', 'Heart Rate'),
                    use_container_width=True
                )
                st.plotly_chart(
                    self._create_vital_signs_chart(df, 'temperature', 'Temperature'),
                    use_container_width=True
                )
                st.plotly_chart(
                    self._create_vital_signs_chart(df, 'spo2', 'SpO2'),
                    use_container_width=True
                )
            
            with col2:
                st.plotly_chart(
                    self._create_vital_signs_chart(df, 'respiratory_rate', 'Respiratory Rate'),
                    use_container_width=True
                )
                st.plotly_chart(
                    self._create_vital_signs_chart(df, 'systolic_bp', 'Systolic BP'),
                    use_container_width=True
                )
                st.plotly_chart(
                    self._create_vital_signs_chart(df, 'diastolic_bp', 'Diastolic BP'),
                    use_container_width=True
                )
        
        with tab2:
            st.header("Recent Alerts")
            
            # Get latest alerts
            latest_vitals = filtered_data[-1]
            alerts, prediction = self.ingestor.analyze_vital_signs(latest_vitals)
            
            # Display alerts table
            alerts_df = self._create_alerts_table(alerts)
            if not alerts_df.empty:
                st.dataframe(alerts_df, use_container_width=True)
            else:
                st.info("No alerts in the selected time range.")
        
        with tab3:
            st.header("Health Risk Analysis")
            
            # Get latest prediction
            latest_vitals = filtered_data[-1]
            _, prediction = self.ingestor.analyze_vital_signs(latest_vitals)
            
            # Display anomaly section
            self._create_anomaly_section(prediction)
            
            # Add trend analysis
            st.subheader("Trend Analysis")
            
            # Calculate basic statistics
            stats_df = df.describe()
            st.write("Statistical Summary:")
            st.dataframe(stats_df, use_container_width=True)
            
            # Add trend indicators
            st.write("Trend Indicators:")
            for vital_sign in ['heart_rate', 'temperature', 'spo2', 'respiratory_rate', 'systolic_bp', 'diastolic_bp']:
                trend = df[vital_sign].diff().mean()
                st.metric(
                    label=vital_sign.replace('_', ' ').title(),
                    value=f"{df[vital_sign].iloc[-1]:.1f}",
                    delta=f"{trend:.1f}"
                )

if __name__ == "__main__":
    dashboard = VitalSignsDashboard()
    dashboard.run() 