#!/usr/bin/env python3
"""
Test the fixes for Streamlit session state and Ollama connection
"""

from vault import IdentityVault
from engine import PrivacyEngine

def test_ollama_connection():
    """Test improved Ollama connection handling."""
    print("🔧 TESTING OLLAMA CONNECTION FIXES")
    print("=" * 50)
    
    try:
        engine = PrivacyEngine()
        
        # Test health check
        print("\n📊 Testing Health Check...")
        health = engine.health_check()
        
        print(f"✅ Vault Connection: {health['vault_connection']}")
        print(f"✅ Ollama Connection: {health['ollama_connection']}")
        print(f"✅ Model Available: {health['model_available']}")
        
        # Test query processing
        print("\n🔄 Testing Query Processing...")
        
        # Create test user
        vault = IdentityVault()
        success, _ = vault.create_user("testuser", "testpass123")
        
        if success:
            user = vault.authenticate_user("testuser", "testpass123")
            if user:
                test_query = "My email is test@example.com. Help me!"
                
                try:
                    result = engine.process_query(test_query, user['id'])
                    print(f"✅ Query processed successfully!")
                    print(f"✅ PII Detected: {result['pii_detected']}")
                    print(f"✅ Processing Time: {result['processing_time']:.2f}s")
                    
                except Exception as e:
                    print(f"❌ Query processing failed: {e}")
            else:
                print("❌ User authentication failed")
        else:
            print("❌ User creation failed")
        
        engine.close()
        vault.close()
        
        print("\n🎯 OLLAMA CONNECTION TEST COMPLETE")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_ollama_connection()
