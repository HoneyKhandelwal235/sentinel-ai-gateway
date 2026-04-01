import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import json
from engine import PrivacyEngine
from vault import IdentityVault

# 1. Configure Page First
st.set_page_config(
    page_title="AI Privacy Gateway",
    page_icon="🔒",
    layout="wide"
)

def initialize_session_state():
    """Initialize all session variables correctly."""
    if 'vault' not in st.session_state:
        st.session_state.vault = IdentityVault()
    if 'privacy_engine' not in st.session_state:
        # Standardize on HuggingFace for Cloud deployment
        st.session_state.privacy_engine = PrivacyEngine(inference_mode="huggingface")
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'session_stats' not in st.session_state:
        st.session_state.session_stats = {
            'queries_processed': 0,
            'pii_blocked': 0,
            'total_processing_time': 0.0
        }

def render_login_page():
    st.title("🔒 Sentinel AI Gateway")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = st.session_state.vault.authenticate_user(username, password)
            if user:
                st.session_state.current_user = user
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid credentials")
                
    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            success, msg = st.session_state.vault.create_user(new_user, new_pass)
            if success:
                st.success("Account created! Please login.")
            else:
                st.error(msg)

def render_sidebar():
    """Fixed Indentation for Sidebar Actions."""
    with st.sidebar:
        st.markdown(f"### 👤 User: {st.session_state.current_user['username']}")
        
        st.divider()
        st.markdown("### 📊 Stats")
        st.metric("PII Blocked", st.session_state.session_stats['pii_blocked'])
        
        st.divider()
        st.markdown("### ⚙️ Actions")
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.vault.clear_user_chat_history(st.session_state.current_user['id'])
            st.rerun()
            
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

def handle_query(user_input):
    """Securely process queries using the privacy engine."""
    user_id = st.session_state.current_user['id']
    try:
        with st.spinner("Protecting PII..."):
            # Save raw message locally
            st.session_state.vault.save_chat_message(user_id, "user", user_input)
            
            # Run through Privacy Engine
            result = st.session_state.privacy_engine.process_query(user_input, user_id=user_id)
            
            # Save protected AI response
            st.session_state.vault.save_chat_message(
                user_id, "ai", result['final_response'], 
                result['pii_detected'], result['processing_time']
            )
            
            # Update Dashboard Stats
            st.session_state.session_stats['queries_processed'] += 1
            st.session_state.session_stats['pii_blocked'] += len(result['pii_detected'])
            st.session_state.session_stats['total_processing_time'] += result['processing_time']
            st.rerun()
    except Exception as e:
        st.error(f"Service Error: {str(e)}")

def render_chat_interface():
    st.markdown("### 💬 Secure Chat")
    user_id = st.session_state.current_user['id']
    history = st.session_state.vault.get_chat_history(user_id)
    
    for msg in reversed(history):
        role = "👤 You" if msg['message_type'] == 'user' else "🤖 AI"
        st.write(f"**{role}:** {msg['content']}")
        if msg.get('pii_detected'):
            st.caption(f"🔒 PII Filtered: {msg['pii_detected']}")

    query = st.chat_input("Enter message...")
    if query:
        handle_query(query)

def main():
    initialize_session_state()
    
    if not st.session_state.authenticated:
        render_login_page()
    else:
        render_sidebar()
        tab1, tab2 = st.tabs(["Chat", "Analytics"])
        with tab1:
            render_chat_interface()
        with tab2:
            st.write("Analytics View Active") # Placeholder to prevent indentation errors

if __name__ == "__main__":
    main()