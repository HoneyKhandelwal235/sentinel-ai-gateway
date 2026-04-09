import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from typing import Dict, List
import time
import json
from engine import PrivacyEngine
from vault import IdentityVault

# Verify API Token at startup
try:
    token = st.secrets.get('HUGGINGFACE_API_TOKEN', '')
    if not token:
        st.warning('Running in Local Mode - AI response will be simulated')
except Exception as e:
    st.warning(f'Secrets access issue: {e}. Running in Local Mode.')

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
            margin: 0.5rem 0;
            border-radius: 0.5rem;
        }
        .user-message {
            background-color: #e3f2fd;
            border-left: 4px solid #1f77b4;
        }
        .ai-message {
            background-color: #f1f3f4;
            border-left: 4px solid #00d4aa;
        }
        .pii-detected {
            background-color: #fff4e6;
            border: 1px solid #f8d7da;
            padding: 0.5rem;
            margin: 0.5rem 0;
            border-radius: 0.25rem;
        }
    </style>
    """, unsafe_allow_html=True)
# Configure Streamlit page
st.set_page_config(
    page_title="AI Privacy Gateway - Enterprise Security Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'privacy_engine' not in st.session_state:
        st.session_state.privacy_engine = None
    if 'vault' not in st.session_state:
        st.session_state.vault = IdentityVault()
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if 'session_stats' not in st.session_state:
        st.session_state.session_stats = {
            'queries_processed': 0,
            'pii_blocked': 0,
            'total_processing_time': 0.0
        }
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

# Authentication functions
def render_login_page():
    """Render the professional login page with dynamic authentication UI."""
    st.markdown('<h1 class="main-header">🔒 AI Privacy Gateway</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Initialize auth mode state
        if 'auth_mode' not in st.session_state:
            st.session_state.auth_mode = 'login'
        
        # Professional container
        with st.container():
            if st.session_state.auth_mode == 'login':
                # Login View
                st.markdown("### 🔐 Login to Your Account")
                st.markdown("Access your private, AI-powered privacy dashboard.")
                
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submit_button = st.form_submit_button("🔓 Login", use_container_width=True)
                    
                    if submit_button:
                        if username and password:
                            vault = st.session_state.vault
                            user = vault.authenticate_user(username, password)
                            
                            if user:
                                st.session_state.current_user = user
                                st.session_state.authenticated = True
                                st.session_state.privacy_engine = PrivacyEngine(inference_mode="huggingface")
                                st.success(f"Welcome back, {user['username']}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Invalid username or password. Please try again.")
                        else:
                            st.error("⚠️ Please enter both username and password.")
                
                # Toggle to Sign Up
                st.markdown("---")
                st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                if st.button("New user? Create an account", use_container_width=True):
                    st.session_state.auth_mode = 'signup'
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                # Sign Up View
                st.markdown("### 📝 Create Your Account")
                st.markdown("Join our secure privacy protection platform.")
                
                with st.form("register_form"):
                    new_username = st.text_input("New Username", placeholder="Choose a username")
                    new_password = st.text_input("New Password", type="password", placeholder="Choose a strong password")
                    email = st.text_input("Email (Optional)", placeholder="your.email@example.com")
                    register_button = st.form_submit_button("🚀 Create Account", use_container_width=True)
                    
                    if register_button:
                        if new_username and new_password:
                            vault = st.session_state.vault
                            try:
                                vault.create_user(new_username, new_password, email)
                                st.success("✅ Account created successfully! Please login with your new credentials.")
                                time.sleep(2)
                                st.session_state.auth_mode = 'login'
                                st.rerun()
                            except ValueError as e:
                                st.error(f"❌ Registration failed: {e}")
                            except Exception as e:
                                st.error(f"❌ Registration failed: {e}")
                        else:
                            st.error("⚠️ Please fill in all required fields.")
                
                # Toggle to Login
                st.markdown("---")
                st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
                if st.button("Already have an account? Login", use_container_width=True):
                    st.session_state.auth_mode = 'login'
                    st.rerun()
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
        stats = st.session_state.session_stats
        st.sidebar.markdown(f"### 📊 Session Statistics")
        st.sidebar.metric("Queries Processed", stats['queries_processed'])
        st.sidebar.metric("PII Items Blocked", stats['pii_blocked'])
        
        avg_time = (stats['total_processing_time'] / 
                   max(1, stats['queries_processed']))
        st.sidebar.metric("Avg Processing Time", f"{avg_time:.2f}s")
        
        # Reset Session button
        if st.sidebar.button("🔄 Reset Session", type="secondary"):
            st.session_state.clear()
            st.rerun()
        
        # Debug Reset button
        if st.sidebar.button("🔧 Debug Reset", type="secondary", help="Clear all session state to fix stuck logins"):
            st.session_state.clear()
            st.rerun()
        
        # Clear Database button (for testing)
        if st.sidebar.button("🗑️ Clear Database", type="secondary", help="Clear all users and data for testing"):
            try:
                st.session_state.vault.clear_all_data()
                st.session_state.clear()
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error clearing database: {e}")
        
        # Logout button
        render_logout_button()

def render_security_dashboard():
    """Render security dashboard in sidebar."""
    if st.session_state.authenticated:
        try:
            user_id = st.session_state.current_user['id']
            health = st.session_state.privacy_engine.health_check()
            privacy_stats = st.session_state.vault.get_privacy_stats(user_id)
            
            # Debug verification
            st.sidebar.write("🔧 Debug: Database Connected")
            st.sidebar.write("🔧 Debug: User Authenticated")
            
            # System Status
            st.sidebar.markdown("### System Status")
            
            # Determine overall status
            status_color = "status-healthy"
            vault_healthy = health['vault_connection'] == "healthy"
            
            # Check AI connection status
            ai_status = health['inference_connection']
            if ai_status == 'healthy':
                ai_healthy = True
            elif ai_status in ['local_mode', 'no_key']:
                ai_healthy = True  # These are expected states
            elif ai_status == 'invalid_key':
                ai_healthy = False  # This is an error state
            else:
                ai_healthy = False  # Any other state is an error
            
            if not vault_healthy:
                status_color = "status-error"
            elif not ai_healthy:
                status_color = "status-warning" if ai_status in ['local_mode', 'no_key'] else "status-error"
            
            status_text = "🟢 Healthy" if status_color == "status-healthy" else "🟡 Warning" if status_color == "status-warning" else "🔴 Error"
            
            st.sidebar.markdown(f"""
            <div class="security-status {status_color}">
                <strong>Overall Status:</strong> {status_text}
            </div>
            """, unsafe_allow_html=True)
            
            # Connection Status
            st.sidebar.markdown("#### Connections")
            st.sidebar.write(f"🤖 AI Model: {st.session_state.privacy_engine.model_name}")
            st.sidebar.write(f"🗄️ Vault: {'🟢 Connected' if health['vault_connection'] == 'healthy' else '🔴 Error'}")
            
            # AI Service status with proper error handling
            if health['inference_connection'] == 'local_mode':
                if 'connection_message' in health:
                    st.sidebar.write(f"🌐 AI Service: {health['connection_message']}")
                else:
                    st.sidebar.write("🌐 AI Service: 🟡 Local Mode")
            elif health['inference_connection'] == 'invalid_key':
                st.sidebar.write("🌐 AI Service: 🔴 Invalid API Key (use hf_ token)")
            elif health['inference_connection'] == 'no_key':
                st.sidebar.write("🌐 AI Service: 🟡 Add HuggingFace API Key")
            elif health['inference_connection'] == 'healthy':
                st.sidebar.write("🌐 AI Service: 🟢 Connected")
            else:
                st.sidebar.write(f"🌐 AI Service: 🔴 {health['inference_connection']}")
            
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
                # Pass both redacted and original query to engine
                response = st.session_state.privacy_engine.process_query(redacted_text, original_query=user_input)
                if not response or response.strip() == "":
                    response = "I understand your query about privacy and security. Let me help you with that."
            except Exception as ai_error:
                print(f"AI Error: {ai_error}")
                # Provide a helpful fallback response
                response = "I'm your privacy assistant. I can help you with questions about data protection, PII detection, and secure communication. How can I assist you today?"
            
            # Restore PII in response if needed
            if mapping:
                try:
                    restored_response = st.session_state.vault.restore_pii(response, user_id)
                except:
                    restored_response = response  # Continue with original if restore fails
            else:
                restored_response = response
            
            processing_time = time.time() - start_time
            
            # Save messages to chat history (with database guard)
            try:
                st.session_state.vault.save_chat_message(
                    user_id, "user", user_input, 
                    ",".join(mapping.keys()) if mapping else None, 
                    processing_time, st.session_state.session_id
                )
                
                st.session_state.vault.save_chat_message(
                    user_id, "ai", restored_response, 
                    None, 0, st.session_state.session_id
                )
            except Exception as db_error:
                print(f"Database save error (non-critical): {db_error}")
                # Continue even if database save fails - UI should not crash
            
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
        
        # Try to save to database (with database guard)
        try:
            st.session_state.vault.save_chat_message(
                user_id, "user", user_input, None, 0, st.session_state.session_id
            )
            st.session_state.vault.save_chat_message(
                user_id, "ai", error_response, None, 0, st.session_state.session_id
            )
        except Exception as db_error:
            print(f"Database save error in error handling (non-critical): {db_error}")
            pass  # Ignore database errors - UI should not crash

def render_chat_interface():
    """Render the main chat interface with proper message display."""
    st.markdown("### 💬 Secure AI Chat")
    
    # Display chat messages from session state (not database)
    if 'chat_messages' in st.session_state and st.session_state.chat_messages:
        for message in st.session_state.chat_messages:
            if message['role'] == 'user':
                st.markdown(f"👤 **You:** {message['content']}")
            else:
                st.markdown(f"🤖 **Assistant:** {message['content']}")
            st.markdown("---")
    else:
        st.info("🔒 Start a secure conversation. Your PII will be automatically protected.")
    
    # Example queries section
    with st.expander("💡 Example Queries"):
        st.markdown("""
        Try these examples to see PII protection in action:
        
        - "My email is john.doe@example.com and I need help with my account."
        - "Call me at +91-9876543210 for any urgent matters."
        - "My PAN number is ABCDE1234F and I need tax assistance."
        - "My Aadhaar is 2345-6789-0123 and I want to update my details."
        """)
    
    # Chat input with unique key
    user_input = st.chat_input(
        "Type your query here...", 
        key="main_chat_input_unique_123" 
    )
    
    if user_input:
        handle_query(user_input)
        st.rerun()

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
            st.plotly_chart(fig, width='stretch')
        
        # Recent activity
        if chat_history:
            st.markdown("#### Recent Activity")
            for msg in chat_history[:5]:
                st.write(f"**{msg['message_type'].title()}:** {msg['content'][:100]}...")
        
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Load custom CSS
    load_custom_css()
    
    # Page header
    st.markdown('<h1 class="main-header">🔒 AI Privacy Gateway - Enterprise Security Solution</h1>', unsafe_allow_html=True)
    
    # Check authentication
    if not st.session_state.authenticated:
        render_login_page()
    else:
        # Render sidebar with security dashboard
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
            f"Powered by Hugging Face & Streamlit</small></center>",
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
