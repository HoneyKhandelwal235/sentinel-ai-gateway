import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
from engine import PrivacyEngine
from vault import IdentityVault

# Fix 1: Ensure unique session initialization
def initialize_session_state():
    if 'vault' not in st.session_state:
        st.session_state.vault = IdentityVault()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'session_stats' not in st.session_state:
        st.session_state.session_stats = {'queries': 0, 'blocked': 0, 'time': 0.0}

def render_sidebar():
    """Corrected Indentation for Sidebar metrics."""
    with st.sidebar:
        st.title("🛡️ Security Center")
        if st.session_state.current_user:
            st.write(f"Logged in: **{st.session_state.current_user['username']}**")
            st.divider()
            st.metric("Queries Processed", st.session_state.session_stats['queries'])
            st.metric("PII Items Blocked", st.session_state.session_stats['blocked'])
            if st.button("🚪 Logout", type="primary"):
                st.session_state.clear()
                st.rerun()

def render_chat_interface():
    """Fixed: Added Unique Key to chat_input."""
    st.markdown("### 💬 Secure AI Interaction")
    # Simplified chat logic for stability
    user_input = st.chat_input("Type safely...", key="secure_chat_input_v1")
    if user_input:
        user_id = st.session_state.current_user['id']
        # Process redaction
        redacted, mapping = st.session_state.vault.redact_with_mapping(user_input, user_id)
        # Get AI response
        engine = PrivacyEngine()
        response = engine.process_query(redacted)
        # Display and Save
        st.write(f"**You:** {user_input}")
        st.info(f"**AI:** {response}")
        if mapping:
            st.warning(f"🔒 PII Filtered: {', '.join(mapping.keys())}")
        st.session_state.session_stats['queries'] += 1
        st.session_state.session_stats['blocked'] += len(mapping)

def main():
    initialize_session_state()
    if not st.session_state.authenticated:
        # Simplified Login for UI stability
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            user = st.session_state.vault.authenticate_user(u, p)
            if user:
                st.session_state.current_user, st.session_state.authenticated = user, True
                st.rerun()
    else:
        render_sidebar()
        render_chat_interface()

if __name__ == "__main__":
    main()