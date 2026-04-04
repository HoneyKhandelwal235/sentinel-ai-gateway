#!/usr/bin/env python3
import streamlit as st
import os

print("🔍 Checking Streamlit Secrets...")

try:
    # Check if secrets exist
    if hasattr(st, 'secrets'):
        print("✅ st.secrets exists")
        
        # Check specific secret
        token = st.secrets.get('HUGGINGFACE_API_TOKEN', '')
        print(f"🔑 Token found: {'Yes' if token else 'No'}")
        print(f"📝 Token length: {len(token)}")
        print(f"🔍 Token starts with hf_: {token.startswith('hf_') if token else 'N/A'}")
        print(f"👀 Token preview: {token[:10]}..." if token else 'No token')
        
        # Check all secrets
        print(f"📋 All secrets: {dict(st.secrets)}")
    else:
        print("❌ st.secrets does not exist")
        
except Exception as e:
    print(f"❌ Error checking secrets: {e}")

# Also check environment variables
env_token = os.environ.get('HUGGINGFACE_API_TOKEN', '')
print(f"🌍 Environment token: {'Yes' if env_token else 'No'}")
if env_token:
    print(f"🔍 Env token starts with hf_: {env_token.startswith('hf_')}")
