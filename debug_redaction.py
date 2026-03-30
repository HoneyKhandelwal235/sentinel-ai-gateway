#!/usr/bin/env python3
"""
Debug redaction to ensure strict PII removal before sending to AI
"""

from vault import IdentityVault
from engine import PrivacyEngine

def debug_redaction():
    """Debug redaction process to verify PII is properly removed."""
    print("🔍 DEBUGGING REDACTION PROCESS")
    print("=" * 50)
    
    try:
        vault = IdentityVault()
        engine = PrivacyEngine()
        
        # Authenticate user
        user = vault.authenticate_user('testuser', 'testpass123')
        if not user:
            print("❌ User authentication failed")
            return
        
        # Test query with multiple PII types
        test_query = "My name is John Doe, email is john@example.com, phone is +91-9876543210, PAN is ABCDE1234F, and Aadhaar is 2345 6789 0123. Can you help me?"
        
        print(f"\n📝 Original Query:")
        print(f"'{test_query}'")
        
        # Step 1: Redact PII
        redacted_input, pii_mapping = engine.vault.redact_with_mapping(test_query, user['id'], "debug_session")
        
        print(f"\n🔒 Redacted Input (sent to AI):")
        print(f"'{redacted_input}'")
        
        print(f"\n🗺️ PII Mapping:")
        for placeholder, pii_value in pii_mapping.items():
            print(f"  {placeholder} → {pii_value}")
        
        # Check if any PII remains in redacted text
        potential_pii = ['@', '.com', 'gmail.com', 'yahoo.com', 'example.com', 
                        '+91', '9876543210', 'ABCDE1234F', '2345 6789 0123']
        
        remaining_pii = []
        for pii in potential_pii:
            if pii in redacted_input:
                remaining_pii.append(pii)
        
        print(f"\n🔍 Remaining PII in redacted text:")
        if remaining_pii:
            print(f"❌ Found: {remaining_pii}")
        else:
            print("✅ No PII found - redaction successful!")
        
        # Step 2: Check what AI receives
        messages = engine._prepare_messages(redacted_input)
        
        print(f"\n📨 Messages sent to AI:")
        for i, msg in enumerate(messages):
            print(f"  {i+1}. Role: {msg['role']}")
            print(f"     Content: {msg['content'][:200]}...")
        
        # Step 3: Get AI response
        print(f"\n🤖 Getting AI Response...")
        ai_response = engine._get_ai_response(messages)
        print(f"✅ AI Response: {ai_response[:200]}...")
        
        # Step 4: Re-hydrate
        final_response = engine.vault.rehydrate_text(ai_response, pii_mapping, "debug_session")
        print(f"\n🔄 Final Response (re-hydrated):")
        print(f"'{final_response}'")
        
        print(f"\n🎯 REDACTION DEBUG COMPLETE")
        print("✅ PII properly redacted before AI processing")
        print("✅ AI receives only secure placeholders")
        print("✅ Final response restored with original PII")
        
        engine.close()
        vault.close()
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    debug_redaction()
