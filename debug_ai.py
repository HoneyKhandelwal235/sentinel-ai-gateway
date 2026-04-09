#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import PrivacyEngine

def debug_ai_response():
    """Debug AI response issue."""
    print("DEBUG: Testing AI Response...")
    
    try:
        # Initialize engine
        engine = PrivacyEngine(inference_mode="huggingface")
        
        print(f"DEBUG: Client initialized: {engine.client is not None}")
        print(f"DEBUG: Connection message: {getattr(engine, 'connection_message', 'None')}")
        
        # Test health check
        health = engine.health_check()
        print(f"DEBUG: Health status: {health}")
        
        # Test the specific query that's failing
        test_query = "My PAN number is ABCDE1234F and I need tax assistance."
        print(f"DEBUG: Testing query: {test_query}")
        
        response = engine.process_query(test_query)
        print(f"DEBUG: AI Response: {response}")
        print(f"DEBUG: Response length: {len(response)}")
        
        # Check if it's a fallback
        fallback_indicators = [
            "I apologize, but I encountered an issue",
            "I can still help you with privacy and security questions",
            "Please try rephrasing your question"
        ]
        
        is_fallback = any(indicator in response for indicator in fallback_indicators)
        print(f"DEBUG: Is fallback: {is_fallback}")
        
        # Test with a simple query
        simple_query = "Hello"
        print(f"DEBUG: Testing simple query: {simple_query}")
        simple_response = engine.process_query(simple_query)
        print(f"DEBUG: Simple response: {simple_response}")
        
        return not is_fallback
        
    except Exception as e:
        print(f"DEBUG: Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_ai_response()
    if success:
        print("\nDEBUG: AI Response Test PASSED")
    else:
        print("\nDEBUG: AI Response Test FAILED")
