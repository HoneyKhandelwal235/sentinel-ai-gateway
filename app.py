import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List
from engine import PrivacyEngine

# Configure Streamlit page
st.set_page_config(
    page_title="AI Privacy Gateway - Enterprise Security Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
def load_custom_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1e3a8a;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .security-status {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .status-healthy {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .status-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        .status-error {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        .user-message {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
        }
        .ai-message {
            background-color: #f3e5f5;
            border-left: 4px solid #9c27b0;
        }
        .pii-detected {
            background-color: #fff3e0;
            border: 1px solid #ffcc02;
            border-radius: 5px;
            padding: 0.5rem;
            margin: 0.5rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'privacy_engine' not in st.session_state:
        st.session_state.privacy_engine = PrivacyEngine()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'session_stats' not in st.session_state:
        st.session_state.session_stats = {
            'queries_processed': 0,
            'pii_blocked': 0,
            'total_processing_time': 0
        }

def render_security_dashboard():
    """Render the security dashboard sidebar."""
    st.sidebar.markdown("## 🔐 Security Dashboard")
    
    # Get dashboard data
    try:
        dashboard_data = st.session_state.privacy_engine.get_privacy_dashboard_data()
        vault_summary = dashboard_data['vault_summary']
        privacy_stats = dashboard_data['privacy_stats']
        
        # System Status
        st.sidebar.markdown("### System Status")
        health = st.session_state.privacy_engine.health_check()
        
        status_color = "status-healthy"
        if "unhealthy" in str(health.values()):
            status_color = "status-error"
        elif any("warning" in str(v).lower() for v in health.values()):
            status_color = "status-warning"
        
        st.sidebar.markdown(f"""
        <div class="security-status {status_color}">
            <strong>Overall Status:</strong> {'🟢 Healthy' if status_color == 'status-healthy' else '🟡 Warning' if status_color == 'status-warning' else '🔴 Error'}
        </div>
        """, unsafe_allow_html=True)
        
        # Connection Status
        st.sidebar.markdown("#### Connections")
        st.sidebar.write(f"🤖 AI Model: {dashboard_data['session_info']['model_name']}")
        st.sidebar.write(f"🗄️ Vault: {'🟢 Connected' if health['vault_connection'] == 'healthy' else '🔴 Error'}")
        st.sidebar.write(f"🌐 Ollama: {'🟢 Connected' if health['ollama_connection'] == 'healthy' else '🔴 Error'}")
        
        # PII Statistics
        st.sidebar.markdown("### 📊 Today's PII Statistics")
        
        if privacy_stats:
            for pii_type, count in privacy_stats.items():
                st.sidebar.metric(f"{pii_type}", count)
        else:
            st.sidebar.write("No PII detected today")
        
        # Vault Summary
        st.sidebar.markdown("### 🗄️ Vault Summary")
        st.sidebar.metric("Total Mappings", vault_summary['total_mappings'])
        
        if vault_summary['type_breakdown']:
            st.sidebar.markdown("**PII Types:**")
            for pii_type, count in vault_summary['type_breakdown'].items():
                st.sidebar.write(f"• {pii_type}: {count}")
        
        # Session Statistics
        st.sidebar.markdown("### 📈 Session Statistics")
        st.sidebar.metric("Queries Processed", st.session_state.session_stats['queries_processed'])
        st.sidebar.metric("PII Items Blocked", st.session_state.session_stats['pii_blocked'])
        
        avg_time = (st.session_state.session_stats['total_processing_time'] / 
                   max(1, st.session_state.session_stats['queries_processed']))
        st.sidebar.metric("Avg Processing Time", f"{avg_time:.2f}s")
        
        # Action Buttons
        st.sidebar.markdown("### ⚙️ Actions")
        
        if st.sidebar.button("🔄 Refresh Dashboard"):
            st.rerun()
        
        if st.sidebar.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
        
        if st.sidebar.button("🔄 New Session"):
            st.session_state.privacy_engine.clear_session_data()
            st.session_state.session_stats = {
                'queries_processed': 0,
                'pii_blocked': 0,
                'total_processing_time': 0
            }
            st.rerun()
        
        if st.sidebar.button("📥 Export Audit Log"):
            audit_data = st.session_state.privacy_engine.export_audit_log()
            st.sidebar.download_button(
                label="Download Audit Log",
                data=json.dumps(audit_data, indent=2, default=str),
                file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
    except Exception as e:
        st.sidebar.error(f"Error loading dashboard: {e}")

def render_chat_interface():
    """Render the main chat interface."""
    st.markdown('<h1 class="main-header">🔒 AI Privacy Gateway</h1>', unsafe_allow_html=True)
    
    # Chat Interface
    st.markdown("### 💬 Secure AI Chat")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message['type'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You:</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message ai-message">
                    <strong>🤖 AI:</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
                
                # Show PII detection info if available
                if message.get('pii_detected'):
                    st.markdown(f"""
                    <div class="pii-detected">
                        <strong>🔒 PII Protected:</strong> {', '.join(message['pii_detected'])}
                    </div>
                    """, unsafe_allow_html=True)
    
    # Input area
    st.markdown("### 📝 Enter Your Query")
    
    # Example queries
    with st.expander("💡 Example Queries"):
        st.write("• My name is John Doe and my email is john@example.com. Can you help me?")
        st.write("• I need to update my PAN number ABCDE1234F and phone +91-9876543210.")
        st.write("• My Aadhaar is 2345 6789 0123. What documents do I need?")
        st.write("• Contact me at priya.patel@company.com for business inquiry.")
    
    # User input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Enter your message:",
            placeholder="Type your query here... PII will be automatically protected.",
            key="user_input"
        )
    
    with col2:
        send_button = st.button("🚀 Send", type="primary")
    
    # Process user input
    if send_button and user_input:
        with st.spinner("🔄 Processing your secure query..."):
            try:
                # Add user message to chat history
                st.session_state.chat_history.append({
                    'type': 'user',
                    'content': user_input,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Process query through privacy engine
                result = st.session_state.privacy_engine.process_query(user_input)
                
                # Add AI response to chat history
                st.session_state.chat_history.append({
                    'type': 'ai',
                    'content': result['final_response'],
                    'pii_detected': result['pii_detected'],
                    'processing_time': result['processing_time'],
                    'timestamp': result['timestamp']
                })
                
                # Update session statistics
                st.session_state.session_stats['queries_processed'] += 1
                st.session_state.session_stats['pii_blocked'] += len(result['pii_detected'])
                st.session_state.session_stats['total_processing_time'] += result['processing_time']
                
                # Clear input
                st.session_state.user_input = ""
                
                # Rerun to update the interface
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error processing your query: {e}")
                st.error("Please check your Ollama connection and try again.")

def render_analytics_tab():
    """Render analytics and reporting tab."""
    st.markdown("### 📊 Privacy Analytics & Reporting")
    
    try:
        # Get audit data
        audit_data = st.session_state.privacy_engine.export_audit_log(1000)
        
        if audit_data:
            # Convert to DataFrame
            df = pd.DataFrame(audit_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Create tabs for different analytics
            tab1, tab2, tab3 = st.tabs(["📈 Activity Trends", "🔍 PII Analysis", "📋 Audit Report"])
            
            with tab1:
                st.markdown("#### Recent Activity Trends")
                
                # Activity over time
                activity_by_hour = df.groupby(df['timestamp'].dt.hour).size().reset_index()
                activity_by_hour.columns = ['Hour', 'Count']
                
                fig = px.bar(
                    activity_by_hour,
                    x='Hour',
                    y='Count',
                    title="Privacy Operations by Hour",
                    color='Count',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Operations breakdown
                operation_counts = df['operation'].value_counts()
                
                fig2 = px.pie(
                    values=operation_counts.values,
                    names=operation_counts.index,
                    title="Operation Types Distribution"
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            with tab2:
                st.markdown("#### PII Type Analysis")
                
                # PII type distribution
                pii_counts = df['pii_type'].value_counts()
                
                fig3 = px.bar(
                    x=pii_counts.index,
                    y=pii_counts.values,
                    title="PII Types Detected",
                    color=pii_counts.values,
                    color_continuous_scale='plasma'
                )
                st.plotly_chart(fig3, use_container_width=True)
                
                # Recent PII detections
                st.markdown("#### Recent PII Detections")
                recent_pii = df[df['operation'] == 'REDACT'].head(10)
                
                if not recent_pii.empty:
                    st.dataframe(
                        recent_pii[['timestamp', 'pii_type', 'placeholder', 'session_id']],
                        use_container_width=True
                        )
                else:
                    st.write("No recent PII detections found.")
            
            with tab3:
                st.markdown("#### Audit Report")
                
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Operations", len(df))
                
                with col2:
                    st.metric("Unique Sessions", df['session_id'].nunique())
                
                with col3:
                    st.metric("PII Types", df['pii_type'].nunique())
                
                with col4:
                    st.metric("Time Range", f"{(df['timestamp'].max() - df['timestamp'].min()).days} days")
                
                # Full audit log
                st.markdown("#### Full Audit Log")
                st.dataframe(df, use_container_width=True)
                
                # Export options
                st.markdown("#### Export Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"privacy_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    json_data = json.dumps(audit_data, indent=2, default=str)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name=f"privacy_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        else:
            st.info("No audit data available yet. Start using the chat interface to generate data.")
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

def main():
    """Main application entry point."""
    load_custom_css()
    initialize_session_state()
    
    # Create main layout
    with st.sidebar:
        render_security_dashboard()
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["💬 Secure Chat", "📊 Analytics"])
    
    with tab1:
        render_chat_interface()
    
    with tab2:
        render_analytics_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<center><small>🔒 AI Privacy Gateway - Enterprise Security Solution | "
        "Powered by Ollama & Streamlit</small></center>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
