from vault import IdentityVault
from engine import PrivacyEngine

vault = IdentityVault()
engine = PrivacyEngine()

# Try to authenticate existing user
user = vault.authenticate_user('testuser', 'testpass123')
if user:
    print('✅ User authenticated successfully')
    
    # Test query processing
    test_query = 'My email is test@example.com. Help me!'
    result = engine.process_query(test_query, user['id'])
    print('✅ Query processed:', result['pii_detected'])
    
    # Test health check
    health = engine.health_check()
    print('✅ Health check:', health['ollama_connection'])
    
else:
    print('❌ Authentication failed')

engine.close()
vault.close()
