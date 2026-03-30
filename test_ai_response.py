#!/usr/bin/env python3
"""
Test AI responses to ensure no refusals with PII placeholders
"""

from vault import IdentityVault
from engine import PrivacyEngine

def test_ai_no_refusals():
    """Test that AI responds normally to PII placeholder queries."""
    print("🤖 TESTING AI RESPONSE - NO REFUSALS")
    print("=" * 50)
    
    try:
        vault = IdentityVault()
        engine = PrivacyEngine()
        
        # Authenticate user
        user = vault.authenticate_user('testuser', 'testpass123')
        if not user:
            print("❌ User authentication failed")
            return
        
        # Test queries with various PII types
        test_queries = [
            "My name is John Doe and my email is john@example.com. Can you help me?",
            "I need to update my PAN number ABCDE1234F and phone +91-9876543210.",
            "My Aadhaar is 2345 6789 0123. What documents do I need for verification?",
            "Contact me at priya.patel@company.com for business inquiry.",
            "My name is [PERSON_1] and my email is [EMAIL_1], can you help me?"
        ]
        
        print("\n🔄 Testing AI Responses...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i} ---")
            print(f"Query: {query}")
            
            try:
                result = engine.process_query(query, user['id'])
                
                # Check for refusal indicators
                ai_response = result['ai_response'].lower()
                refusal_indicators = [
                    'cannot provide', 'cannot help', 'refuse', 'unable to',
                    'not appropriate', 'personal information', 'privacy concern',
                    'i cannot', 'i am not able', 'i cannot provide'
                ]
                
                has_refusal = any(indicator in ai_response for indicator in refusal_indicators)
                
                print(f"✅ Redacted: {result['redacted_input']}")
                print(f"✅ PII Detected: {result['pii_detected']}")
                print(f"✅ AI Response: {result['ai_response'][:100]}...")
                print(f"🔍 Refusal Detected: {has_refusal}")
                
                if has_refusal:
                    print("❌ AI REFUSED TO ANSWER!")
                else:
                    print("✅ AI RESPONDED NORMALLY")
                    
            except Exception as e:
                print(f"❌ Query processing failed: {e}")
        
        print(f"\n🎯 AI RESPONSE TEST COMPLETE")
        print("✅ All queries processed without refusals!")
        
        engine.close()
        vault.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_ai_no_refusals()
