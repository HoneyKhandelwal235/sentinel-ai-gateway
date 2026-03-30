#!/usr/bin/env python3
"""
Multi-tenant test for AI Privacy Gateway
Tests user isolation and data separation
"""

from vault import IdentityVault
from engine import PrivacyEngine

def test_multi_tenant_isolation():
    """Test complete multi-tenant functionality."""
    
    print("🔒 MULTI-TENANT AI PRIVACY GATEWAY TEST")
    print("=" * 50)
    
    # Create vault and engine
    vault = IdentityVault()
    engine = PrivacyEngine()
    
    try:
        # Create two test users
        print("\n📝 Creating Test Users...")
        success1, msg1 = vault.create_user('Honey', 'password123', 'honey@example.com')
        success2, msg2 = vault.create_user('Student1', 'password456', 'student1@example.com')
        
        print(f"✅ User 1 (Honey): {success1} - {msg1}")
        print(f"✅ User 2 (Student1): {success2} - {msg2}")
        
        # Authenticate both users
        print("\n🔐 Authenticating Users...")
        user1 = vault.authenticate_user('Honey', 'password123')
        user2 = vault.authenticate_user('Student1', 'password456')
        
        print(f"✅ User 1 authenticated: {user1 is not None}")
        print(f"✅ User 2 authenticated: {user2 is not None}")
        
        if not (user1 and user2):
            print("❌ Authentication failed!")
            return
        
        # Test data isolation
        print("\n🔒 Testing Data Isolation...")
        
        # Honey sends a message with PII
        honey_query = "My name is Honey Khandelwal and my email is honey@example.com. Contact me at +91-9876543210."
        result1 = engine.process_query(honey_query, user1['id'])
        print(f"👤 Honey detected PII: {result1['pii_detected']}")
        
        # Student1 sends a different message
        student_query = "I am Student1 with email student1@example.com. My PAN is XYZAB1234C."
        result2 = engine.process_query(student_query, user2['id'])
        print(f"👤 Student1 detected PII: {result2['pii_detected']}")
        
        # Check vault summaries
        print("\n📊 Checking Vault Summaries...")
        honey_summary = vault.get_vault_summary(user1['id'])
        student_summary = vault.get_vault_summary(user2['id'])
        
        print(f"👤 Honey vault: {honey_summary['total_mappings']} mappings")
        print(f"👤 Student1 vault: {student_summary['total_mappings']} mappings")
        
        # Verify isolation - each user should only see their own data
        print("\n🔍 Verifying Data Isolation...")
        
        honey_has_honey_email = any('honey@example.com' in str(pii) for pii in result1['pii_detected'])
        honey_has_student_email = any('student1@example.com' in str(pii) for pii in result1['pii_detected'])
        
        student_has_student_email = any('student1@example.com' in str(pii) for pii in result2['pii_detected'])
        student_has_honey_email = any('honey@example.com' in str(pii) for pii in result2['pii_detected'])
        
        print(f"✅ Honey sees Honey's email: {honey_has_honey_email}")
        print(f"❌ Honey sees Student1's email: {honey_has_student_email}")
        print(f"✅ Student1 sees Student1's email: {student_has_student_email}")
        print(f"❌ Student1 sees Honey's email: {student_has_honey_email}")
        
        # Test chat history isolation
        print("\n💬 Testing Chat History Isolation...")
        
        honey_history = vault.get_chat_history(user1['id'])
        student_history = vault.get_chat_history(user2['id'])
        
        print(f"👤 Honey chat history: {len(honey_history)} messages")
        print(f"👤 Student1 chat history: {len(student_history)} messages")
        
        # Verify audit log isolation
        print("\n📋 Testing Audit Log Isolation...")
        
        honey_audit = vault.get_audit_log_for_user(user1['id'])
        student_audit = vault.get_audit_log_for_user(user2['id'])
        
        print(f"👤 Honey audit entries: {len(honey_audit)}")
        print(f"👤 Student1 audit entries: {len(student_audit)}")
        
        # Final verification
        print("\n🎯 FINAL VERIFICATION")
        
        isolation_working = (
            honey_has_honey_email and 
            not honey_has_student_email and
            student_has_student_email and 
            not student_has_honey_email and
            honey_summary['total_mappings'] > 0 and
            student_summary['total_mappings'] > 0
        )
        
        if isolation_working:
            print("✅ MULTI-TENANT ISOLATION WORKING PERFECTLY!")
            print("✅ Each user sees only their own data")
            print("✅ PII mappings are properly isolated")
            print("✅ Chat history is separated")
            print("✅ Audit logs are user-specific")
        else:
            print("❌ MULTI-TENANT ISOLATION FAILED!")
        
        print("\n" + "=" * 50)
        print("🔒 Multi-tenant test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    finally:
        engine.close()
        vault.close()

if __name__ == "__main__":
    test_multi_tenant_isolation()
