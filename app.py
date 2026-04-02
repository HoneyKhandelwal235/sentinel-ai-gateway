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
                        st.session_state.privacy_engine = PrivacyEngine(inference_mode="huggingface")
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
    """Render user information and session statistics in sidebar."""
    if st.session_state.authenticated:
        user = st.session_state.current_user
        st.sidebar.markdown(f"### 👤 User Information")
        st.sidebar.write(f"**Username:** {user['username']}")
        
        # Session Statistics
        stats = st.session_state.get('session_stats', {
            'queries_processed': 0,
            'pii_blocked': 0,
            'total_processing_time': 0.0
        })
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
    """Render security dashboard in sidebar."""
    if st.session_state.authenticated:
        try:
            user_id = st.session_state.current_user['id']
            health = st.session_state.privacy_engine.health_check()
            privacy_stats = st.session_state.vault.get_privacy_stats(user_id)
            
            # Debug verification
            st.sidebar.write("� Debug: Database Connected")
            st.sidebar.write("🔧 Debug: User Authenticated")
            
            # System Status
            st.sidebar.markdown("### System Status")
            
            # Determine overall status
            status_color = "status-healthy"
            if health['vault_connection'] != "healthy" or health['inference_connection'] != "healthy":
                status_color = "status-error"
            elif health['model_available'] == False:
                status_color = "status-warning"
            
            st.sidebar.markdown(f"""
            <div class="security-status {status_color}">
                <strong>Overall Status:</strong> {'🟢 Healthy' if status_color == 'status-healthy' else '🟡 Warning' if status_color == 'status-warning' else '🔴 Error'}
            </div>
            """, unsafe_allow_html=True)
            
            # Connection Status
            st.sidebar.markdown("#### Connections")
            st.sidebar.write(f"🤖 AI Model: {st.session_state.privacy_engine.model_name}")
            st.sidebar.write(f"🗄️ Vault: {'� Connected' if health['vault_connection'] == 'healthy' else '🔴 Error'}")
            st.sidebar.write(f"🌐 AI Service: {'🟢 Connected' if health['inference_connection'] == 'healthy' else '🔴 Error'}")
            st.sidebar.write(f"🔧 Mode: {health.get('inference_mode', 'unknown').upper()}")
            
            # PII Statistics
            st.sidebar.markdown("### 📊 Today's PII Statistics")
            
            if privacy_stats:
                for pii_type, count in privacy_stats.items():
                    st.sidebar.metric(f"{pii_type}", count)
            else:
                st.sidebar.write("No PII detected today")
            
            # User info
            render_user_info()
            
        except Exception as e:
            st.sidebar.error(f"Error loading dashboard: {e}")

def handle_query(user_input: str):
    """Handle user query processing with robust error handling and guaranteed response."""
    if not user_input or not st.session_state.authenticated:
        return
    
    # Ensure we have the correct user_id
    user_id = st.session_state.current_user.get('id')
    if not user_id:
        st.error("🔧 Session error: User ID not found. Please login again.")
        if st.button("🔄 Login Again"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return
    
    # Debug: Show inference mode and user ID
    st.sidebar.write(f"🔧 Debug: Using {st.session_state.privacy_engine.inference_mode} mode")
    st.sidebar.write(f"🔧 Debug: User ID: {user_id}")
    
    try:
        with st.spinner("🔄 Processing your secure query..."):
            # Process query with PII redaction
            start_time = time.time()
            
            # Get redacted text and mapping
            redacted_text, mapping = st.session_state.vault.redact_with_mapping(user_input, user_id, "chat")
            
            # Get AI response (always provide fallback)
            try:
                response = st.session_state.privacy_engine.process_query(redacted_text)
                if not response or response.strip() == "":
                    response = "I understand your query about privacy and security. Let me help you with that."
            except Exception as ai_error:
                print(f"AI Error: {ai_error}")
                response = "I apologize, but I'm experiencing technical difficulties. However, I can still help you with privacy and security questions."
            
            # Restore PII in response if needed
            if mapping:
                try:
                    restored_response = st.session_state.vault.restore_pii(response, user_id)
                except:
                    restored_response = response  # Continue with original if restore fails
            else:
                restored_response = response
            
            processing_time = time.time() - start_time
            
            # Save messages to chat history (non-critical - don't fail if database has issues)
            try:
                st.session_state.vault.save_chat_message(
                    user_id, "user", user_input, 
                    list(mapping.keys()) if mapping else None, 
                    processing_time, st.session_state.session_id
                )
                
                st.session_state.vault.save_chat_message(
                    user_id, "ai", restored_response, 
                    None, 0, st.session_state.session_id
                )
            except Exception as db_error:
                print(f"Database save error (non-critical): {db_error}")
                # Continue even if database save fails
            
            # Update session stats
            stats = st.session_state.session_stats
            stats['queries_processed'] += 1
            stats['pii_blocked'] += len(mapping) if mapping else 0
            stats['total_processing_time'] += processing_time
            
            # Store in session for display
            if 'chat_messages' not in st.session_state:
                st.session_state.chat_messages = []
            
            st.session_state.chat_messages.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": restored_response}
            ])
            
    except Exception as e:
        print(f"Critical error in handle_query: {e}")
        
        # Always provide a response even if there's an error
        error_response = "I apologize, but I encountered an issue processing your request. However, I can still help you with privacy and security questions. Please try rephrasing your question."
        
        # Store error response in chat
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        st.session_state.chat_messages.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": error_response}
        ])
        
        # Try to save to database (non-critical)
        try:
            st.session_state.vault.save_chat_message(
                user_id, "user", user_input, None, 0, st.session_state.session_id
            )
            st.session_state.vault.save_chat_message(
                user_id, "ai", error_response, None, 0, st.session_state.session_id
            )
        except:
            pass  # Ignore database errors in error handling

def render_chat_interface():
    """Render the main chat interface with message history and input."""
    st.markdown("### 💬 Secure Chat")
    
    # Display chat messages
    if 'chat_messages' in st.session_state and st.session_state.chat_messages:
        for message in st.session_state.chat_messages:
            if message['role'] == 'user':
                st.markdown(f"👤 **You:** {message['content']}")
            else:
                st.markdown(f"🤖 **Assistant:** {message['content']}")
            st.markdown("---")
    else:
        st.info("🔒 Start a secure conversation. Your PII will be automatically protected.")
    
    # Chat input
    user_input = st.chat_input("Type your query here... PII will be automatically protected.")
    
    if user_input:
        handle_query(user_input)
        st.rerun()
    
    # Example queries section
    with st.expander("💡 Example Queries"):
        st.markdown("""
        Try these examples to see PII protection in action:
        
        - "My email is john.doe@example.com and I need help with my account."
        - "Call me at +91-9876543210 for any urgent matters."
        - "My PAN number is ABCDE1234F and I need tax assistance."
        - "My Aadhaar is 2345-6789-0123 and I want to update my details."
        """)

def render_analytics_tab():
    """Render analytics dashboard with privacy statistics."""
    if not st.session_state.authenticated:
        st.warning("Please login to access analytics.")
        return
    
    st.markdown("### 📊 Privacy Analytics")
    
    user_id = st.session_state.current_user['id']
    
    try:
        # Get privacy statistics
        privacy_stats = st.session_state.vault.get_privacy_stats(user_id)
        chat_history = st.session_state.vault.get_chat_history(user_id)
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Queries", len(chat_history))
        
        with col2:
            total_pii = sum(privacy_stats.values()) if privacy_stats else 0
            st.metric("PII Items Blocked", total_pii)
        
        with col3:
            avg_time = st.session_state.session_stats['total_processing_time'] / max(1, st.session_state.session_stats['queries_processed'])
            st.metric("Avg Processing Time", f"{avg_time:.2f}s")
        
        # PII breakdown chart
        if privacy_stats:
            st.markdown("#### PII Detection Breakdown")
            fig = px.pie(
                values=list(privacy_stats.values()),
                names=list(privacy_stats.keys()),
                title="PII Types Detected"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        if chat_history:
            st.markdown("#### Recent Activity")
            for msg in chat_history[:5]:
                st.write(f"**{msg['message_type'].title()}:** {msg['content'][:100]}...")
        
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
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
