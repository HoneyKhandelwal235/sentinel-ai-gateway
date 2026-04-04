#!/usr/bin/env python3
import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import PrivacyEngine
from vault import IdentityVault

def test_pii_system():
    """Test complete PII detection and database updates."""
    print("🔍 Testing PII System...")
    
    try:
        # Clean database
        if os.path.exists('identity_vault.db'):
            os.remove('identity_vault.db')
            print("🧹 Cleaned existing database")
        
        # Initialize vault and engine
        vault = IdentityVault()
        engine = PrivacyEngine(inference_mode="huggingface")
        
        print(f"🤖 Model: {engine.model_name}")
        print(f"🔧 Client: {'Initialized' if engine.client else 'None'}")
        
        # Create a test user
        vault.create_user("testuser", "testpass", "test@example.com")
        print("✅ Created test user")
        
        # Get user ID
        user = vault.authenticate_user("testuser", "testpass")
        user_id = user['id']
        print(f"👤 User ID: {user_id}")
        
        # Test PII query
        test_query = "My Aadhaar is 1234-5678-9012 and I want to update my details"
        print(f"💬 Testing PII Query: {test_query}")
        
        # Process query
        response = engine.process_query(test_query)
        print(f"🤖 AI Response: {response}")
        
        # Check PII detection
        redacted, mapping = vault.redact_with_mapping(test_query, user_id, "test")
        print(f"🔒 Redacted Text: {redacted}")
        print(f"🗺️ PII Mapping: {mapping}")
        
        # Check statistics
        stats = vault.get_privacy_stats(user_id)
        print(f"📊 PII Statistics: {stats}")
        
        # Check database directly
        conn = sqlite3.connect('identity_vault.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pii_mappings WHERE user_id = ?", (user_id,))
        pii_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = ?", (user_id,))
        chat_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"🗄️ Database PII Count: {pii_count}")
        print(f"💬 Database Chat Count: {chat_count}")
        
        # Evaluate results
        if pii_count > 0:
            print("✅ PII Successfully stored in database")
        else:
            print("❌ PII Not stored in database")
            
        if "AADHAAR" in str(stats):
            print("✅ PII Statistics updated correctly")
        else:
            print("❌ PII Statistics not updated")
            
        # Check if response is fallback
        fallback_indicators = [
            "I'm your privacy assistant",
            "Since we're running in local mode"
        ]
        
        is_fallback = any(indicator in response for indicator in fallback_indicators)
        
        if not is_fallback:
            print("✅ Real AI Response (not fallback)")
            return True
        else:
            print("❌ Fallback Response detected")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pii_system()
    if success:
        print("\n🎉 PII SYSTEM TEST: PASSED")
        sys.exit(0)
    else:
        print("\n🚨 PII SYSTEM TEST: FAILED")
        sys.exit(1)
