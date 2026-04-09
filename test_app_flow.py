#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import PrivacyEngine
from vault import IdentityVault

def test_app_flow():
    """Test the exact flow that the app uses."""
    print("TEST: App Flow Simulation...")
    
    try:
        # Initialize vault and engine (like app does)
        vault = IdentityVault()
        engine = PrivacyEngine(inference_mode="huggingface")
        
        # Create test user (like app does)
        vault.create_user("testuser2", "testpass", "test2@example.com")
        user = vault.authenticate_user("testuser2", "testpass")
        user_id = user['id']
        
        print(f"TEST: User ID: {user_id}")
        
        # Simulate the exact app flow
        user_input = "My Aadhaar is 2345-6789-0123 and I want to update my details"
        print(f"TEST: User Input: {user_input}")
        
        # Step 1: Redact PII (like app does)
        redacted_text, mapping = vault.redact_with_mapping(user_input, user_id, "chat")
        print(f"TEST: Redacted Text: {redacted_text}")
        print(f"TEST: Mapping: {mapping}")
        
        # Step 2: Get AI response (like app does)
        response = engine.process_query(redacted_text, original_query=user_input)
        print(f"TEST: AI Response: {response}")
        
        # Step 3: Check if it's the old fallback
        old_fallback = "I apologize, but I encountered an issue processing your request. However, I can still help you with privacy and security questions. Please try rephrasing your question."
        
        if response == old_fallback:
            print("TEST: FAILED - Still getting old fallback")
            return False
        else:
            print("TEST: PASSED - Getting new contextual response")
            return True
            
    except Exception as e:
        print(f"TEST: ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_flow()
    if success:
        print("\nTEST: App Flow Simulation PASSED")
    else:
        print("\nTEST: App Flow Simulation FAILED")
