import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List
from engine import PrivacyEngine
from vault import IdentityVault

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
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .auth-header {
            text-align: center;
            color: #1e3a8a;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'vault' not in st.session_state:
        st.session_state.vault = IdentityVault()
    
    if 'privacy_engine' not in st.session_state:
        st.session_state.privacy_engine = None
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'session_stats' not in st.session_state:
        st.session_state.session_stats = {
            'queries_processed': 0,
            'pii_blocked': 0,
            'total_processing_time': 0
        }

def render_login_page():
    """Render the login/signup page."""
    st.markdown('<div class="auth-header"><h1>🔒 Sentinel AI Gateway</h1><p>Enterprise Privacy Protection</p></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            st.subheader("Login to Your Account")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("🚀 Login", type="primary"):
                if username and password:
                    user = st.session_state.vault.authenticate_user(username, password)
                    if user:
                        st.session_state.current_user = user
                        st.session_state.authenticated = True
                        st.session_state.privacy_engine = PrivacyEngine()
                        st.success(f"Welcome back, {user['username']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            st.subheader("Create New Account")
            new_username = st.text_input("Username", key="signup_username")
            new_email = st.text_input("Email (Optional)", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            if st.button("� Create Account", type="primary"):
                if new_username and new_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, message = st.session_state.vault.create_user(
                            new_username, new_password, new_email if new_email else None
                        )
                        if success:
                            st.success("Account created successfully! Please login.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.warning("Please fill in all required fields")
            
            st.markdown('</div>', unsafe_allow_html=True)

def render_logout_button():
    """Render logout button in sidebar."""
    if st.session_state.authenticated and st.session_state.current_user:
        if st.sidebar.button("🚪 Logout", type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            initialize_session_state()
            st.rerun()

def render_user_info():
    """Render user information in sidebar."""
    if st.session_state.authenticated and st.session_state.current_user:
        st.sidebar.markdown("### 👤 User Information")
        user = st.session_state.current_user
        st.sidebar.write(f"**Username:** {user['username']}")
        if user['email']:
            st.sidebar.write(f"**Email:** {user['email']}")
        
        # Clear Cache button
        if st.sidebar.button("🗑️ Clear Cache", type="secondary", key="clear_cache_btn"):
            # Clear all session state except authentication
            keys_to_keep = ['current_user', 'authenticated', 'vault', 'privacy_engine']
            keys_to_clear = [key for key in st.session_state.keys() if key not in keys_to_keep]
            
            for key in keys_to_clear:
                del st.session_state[key]
            
            # Reset session stats
            st.session_state.session_stats = {
                'queries_processed': 0,
                'pii_blocked': 0,
                'total_processing_time': 0.0
            }
            
            st.sidebar.success("✅ Cache cleared successfully!")
            st.rerun()
        
        # Session stats
        st.sidebar.markdown("### 📊 Session Statistics")
        st.sidebar.metric("Queries Processed", st.session_state.session_stats['queries_processed'])
        st.sidebar.metric("PII Items Blocked", st.session_state.session_stats['pii_blocked'])
        
        avg_time = (st.session_state.session_stats['total_processing_time'] / 
                   max(1, st.session_state.session_stats['queries_processed']))
        st.sidebar.metric("Avg Processing Time", f"{avg_time:.2f}s")

def render_security_dashboard():
    """Render the security dashboard sidebar."""
    st.sidebar.markdown("## 🔐 Security Dashboard")
    
    # User info and logout
    render_user_info()
    render_logout_button()
    
    if not st.session_state.authenticated:
        return
    
    # Get dashboard data
    try:
        user_id = st.session_state.current_user['id']
        vault_summary = st.session_state.vault.get_vault_summary(user_id)
        privacy_stats = vault_summary['today_stats']
        
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
        st.sidebar.write(f"🤖 AI Model: {st.session_state.privacy_engine.model_name}")
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
        
        # Action Buttons
        st.sidebar.markdown("### ⚙️ Actions")
        
        if st.sidebar.button("🔄 Refresh Dashboard"):
            st.rerun()
        
        if st.sidebar.button("🗑️ Clear Chat History"):
            user_id = st.session_state.current_user['id']
            st.session_state.vault.clear_user_chat_history(user_id)
            st.success("Chat history cleared!")
            time.sleep(1)
            st.rerun()
        
        if st.sidebar.button("🔄 New Session"):
            st.session_state.privacy_engine.clear_session_data()
            st.session_state.session_stats = {
                'queries_processed': 0,
                'pii_blocked': 0,
                'total_processing_time': 0
            }
            st.success("New session started!")
            time.sleep(1)
            st.rerun()
        
        if st.sidebar.button("📥 Export Audit Log"):
            user_id = st.session_state.current_user['id']
            audit_data = st.session_state.vault.get_audit_log_for_user(user_id)
            st.sidebar.download_button(
                label="Download Audit Log",
                data=json.dumps(audit_data, indent=2, default=str),
                file_name=f"audit_log_{user['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
    except Exception as e:
        st.sidebar.error(f"Error loading dashboard: {e}")

def handle_query(user_input: str):
    """Handle user query processing with proper session state management and graceful fallbacks."""
    if not user_input or not st.session_state.authenticated:
        return
    
    user_id = st.session_state.current_user['id']
    
    try:
        with st.spinner("🔄 Processing your secure query..."):
            # Save user message to chat history
            st.session_state.vault.save_chat_message(
                user_id, "user", user_input, session_id=st.session_state.privacy_engine.session_id
            )
            
            # Process query through privacy engine
            result = st.session_state.privacy_engine.process_query(
                user_input, user_id=user_id
            )
            
            # Save AI response to chat history
            st.session_state.vault.save_chat_message(
                user_id, "ai", result['final_response'], 
                result['pii_detected'], result['processing_time'], 
                st.session_state.privacy_engine.session_id
            )
            
            # Update session statistics
            st.session_state.session_stats['queries_processed'] += 1
            st.session_state.session_stats['pii_blocked'] += len(result['pii_detected'])
            st.session_state.session_stats['total_processing_time'] += result['processing_time']
            
            # Force rerun to update interface
            st.rerun()
            
    except RuntimeError as e:
        if "Cannot connect to Ollama service" in str(e) or "AI model error" in str(e):
            st.error("🔧 **Service Temporarily Unavailable**")
            st.warning("The AI service is currently experiencing issues. Please try again in a few minutes.")
            st.info("Your message has been saved locally and will be processed when the service is restored.")
        else:
            st.error(f"❌ Error processing your query: {e}")
            st.error("Please try again or contact support if the issue persists.")
            
    except Exception as e:
        st.error("🔧 **Service Temporarily Unavailable**")
        st.warning("An unexpected error occurred. The system has been notified and is working to resolve this issue.")
        st.info("Please try again in a few moments. Your data is secure and protected.")
        
        # Log the error for debugging (in production, this would go to a monitoring service)
        print(f"Unexpected error in handle_query: {e}")

def render_chat_interface():
    """Render the main chat interface with modern chat widgets."""
    st.markdown('<h1 class="main-header">🔒 AI Privacy Gateway</h1>', unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        st.warning("Please login to access chat interface.")
        return
    
    # Chat Interface
    st.markdown("### 💬 Secure AI Chat")
    
    # Load user's chat history
    user_id = st.session_state.current_user['id']
    chat_history = st.session_state.vault.get_chat_history(user_id)
    
    # Display chat history (in reverse order)
    chat_container = st.container()
    with chat_container:
        for message in reversed(chat_history):
            if message['message_type'] == 'user':
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
    
    # Input area with modern chat widget
    st.markdown("### 📝 Enter Your Query")
    
    # Example queries
    with st.expander("💡 Example Queries"):
        st.write("• My name is John Doe and my email is john@example.com. Can you help me?")
        st.write("• I need to update my PAN number ABCDE1234F and phone +91-9876543210.")
        st.write("• My Aadhaar is 2345 6789 0123. What documents do I need?")
        st.write("• Contact me at priya.patel@company.com for business inquiry.")
    
    # Modern chat input widget
    user_input = st.chat_input(
        "Type your query here... PII will be automatically protected.",
        key="chat_input"
    )
    
    # Handle user input through callback
    if user_input:
        handle_query(user_input)

def render_analytics_tab():
    """Render analytics and reporting tab."""
    st.markdown("### 📊 Privacy Analytics & Reporting")
    
    if not st.session_state.authenticated:
        st.warning("Please login to access analytics.")
        return
    
    try:
        user_id = st.session_state.current_user['id']
        audit_data = st.session_state.vault.get_audit_log_for_user(user_id)
        
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
            
          # Sidebar with user info and actions
                st.markdown("#### Export Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"privacy_audit_{st.session_state.current_user['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    json_data = json.dumps(audit_data, indent=2, default=str)
                    st.download_button(
                        label="📥 Download JSON",
                        data=json_data,
                        file_name=f"privacy_audit_{st.session_state.current_user['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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
    
    # Check authentication
    if not st.session_state.authenticated:
        render_login_page()
        return
    
    # Create main layout with authenticated user
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
        f"<center><small>🔒 AI Privacy Gateway - Enterprise Security Solution | "
        f"Logged in as: {st.session_state.current_user['username']} | "
        "Powered by Ollama & Streamlit</small></center>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
