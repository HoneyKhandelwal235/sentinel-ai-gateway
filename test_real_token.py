#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock a real HuggingFace token for testing
import streamlit as st

# Save original secrets
original_secrets = {}
if hasattr(st, 'secrets'):
    original_secrets = dict(st.secrets)

# Mock real token
st.secrets = {
    'HUGGINGFACE_API_TOKEN': 'hf_1234567890abcdefghijklmnopqrstuvwxyz'  # Mock real token format
}

from engine import PrivacyEngine

def test_with_real_token_format():
    """Test with a real HuggingFace token format."""
    print("🔍 Testing with Real Token Format...")
    
    try:
        # Initialize engine
        engine = PrivacyEngine(inference_mode="huggingface")
        
        print(f"🤖 Model: {engine.model_name}")
        print(f"🔧 Client: {'Initialized' if engine.client else 'None'}")
        print(f"📝 Connection Message: {getattr(engine, 'connection_message', 'None')}")
        
        # Test health check
        health = engine.health_check()
        print(f"📊 Health Status: {health}")
        
        # Test actual AI query
        test_query = "Hello, can you help me with privacy questions?"
        print(f"💬 Testing Query: {test_query}")
        
        response = engine.process_query(test_query)
        print(f"🤖 AI Response: {response}")
        
        # Check if response is a fallback
        fallback_indicators = [
            "I'm your privacy assistant",
            "I can help you with questions",
            "I understand you're asking",
            "Since we're running in local mode",
            "I apologize, but I encountered an issue"
        ]
        
        is_fallback = any(indicator in response for indicator in fallback_indicators)
        
        if is_fallback:
            print("❌ RESULT: Fallback response detected")
            return False
        else:
            print("✅ RESULT: Real AI response detected")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    finally:
        # Restore original secrets
        if original_secrets:
            st.secrets = original_secrets

if __name__ == "__main__":
    success = test_with_real_token_format()
    if success:
        print("\n🎉 REAL TOKEN FORMAT TEST: PASSED")
        sys.exit(0)
    else:
        print("\n🚨 REAL TOKEN FORMAT TEST: FAILED")
        sys.exit(1)
