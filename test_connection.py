#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import PrivacyEngine
from vault import IdentityVault

def test_ai_connection():
    """Test AI connection and get real response from HuggingFace."""
    print("🔍 Testing AI Connection...")
    
    try:
        # Initialize vault
        vault = IdentityVault()
        
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

if __name__ == "__main__":
    success = test_ai_connection()
    if success:
        print("\n🎉 CONNECTION TEST: PASSED")
        sys.exit(0)
    else:
        print("\n🚨 CONNECTION TEST: FAILED")
        sys.exit(1)
