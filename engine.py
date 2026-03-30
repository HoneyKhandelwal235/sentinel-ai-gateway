import ollama
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from vault import IdentityVault

class PrivacyEngine:
    """
    Enterprise Privacy Engine that orchestrates PII redaction,
    AI model interaction, and response re-hydration.
    """
    
    def __init__(self, model_name: str = "llama3.2:1b", vault_path: str = "identity_vault.db"):
        self.model_name = model_name
        self.vault = IdentityVault(vault_path)
        self.session_id = str(uuid.uuid4())
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Verify Ollama connection
        self._verify_ollama_connection()
    
    def _verify_ollama_connection(self):
        """Verify Ollama service is available and model exists."""
        try:
            # List available models
            models = ollama.list()
            available_models = []
            
            # Handle different response formats
            if 'models' in models:
                available_models = [model.get('name', model.get('model', 'unknown')) for model in models['models']]
            elif 'models' in str(models):
                # Fallback parsing
                available_models = ['llama3.2:1b']  # Assume model exists
            
            self.logger.info(f"Available models: {available_models}")
            
            if self.model_name not in available_models and len(available_models) > 0:
                self.logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                self.logger.info(f"Pulling model {self.model_name}...")
                ollama.pull(self.model_name)
            
            self.logger.info(f"Ollama connection verified. Using model: {self.model_name}")
            
        except Exception as e:
            self.logger.warning(f"Could not verify Ollama connection: {e}")
            self.logger.info("Continuing without Ollama verification - will attempt connection during use")
    
    def process_query(self, user_input: str, context: Optional[str] = None) -> Dict:
        """
        Process user query through the complete privacy pipeline.
        
        Args:
            user_input: The user's query text
            context: Optional context for the conversation
            
        Returns:
            Dict containing:
            - original_input: Original user input
            - redacted_input: PII-redacted input sent to AI
            - ai_response: Raw AI response
            - final_response: Re-hydrated response with PII restored
            - pii_detected: List of detected PII
            - processing_time: Total processing time in seconds
            - session_id: Current session identifier
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Redact PII from user input
            redacted_input, pii_mapping = self.vault.redact_with_mapping(user_input, self.session_id)
            
            # Step 2: Prepare messages for AI model
            messages = self._prepare_messages(redacted_input, context)
            
            # Step 3: Get response from AI model
            ai_response = self._get_ai_response(messages)
            
            # Step 4: Re-hydrate AI response
            final_response = self.vault.rehydrate_text(ai_response, pii_mapping, self.session_id)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "original_input": user_input,
                "redacted_input": redacted_input,
                "ai_response": ai_response,
                "final_response": final_response,
                "pii_detected": list(pii_mapping.values()),
                "pii_mapping": pii_mapping,
                "processing_time": processing_time,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Query processed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            raise
    
    def _prepare_messages(self, redacted_input: str, context: Optional[str] = None) -> List[Dict]:
        """Prepare messages for AI model with system prompt and context."""
        system_prompt = self._get_system_prompt()
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": redacted_input})
        
        return messages
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the AI model."""
        return """You are a helpful AI assistant. The user's input may contain placeholders 
        like [PERSON_xxxx], [EMAIL_xxxx], [PHONE_xxxx], [PAN_xxxx], or [AADHAAR_xxxx] 
        instead of actual personal information. These placeholders represent sensitive data 
        that has been redacted for privacy. Please respond naturally while keeping these 
        placeholders intact. Do not try to interpret or modify the placeholders."""
    
    def _get_ai_response(self, messages: List[Dict]) -> str:
        """Get response from Ollama AI model."""
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages
            )
            return response['message']['content']
            
        except Exception as e:
            self.logger.error(f"Error getting AI response: {e}")
            raise RuntimeError(f"AI model error: {e}")
    
    def batch_process(self, queries: List[str]) -> List[Dict]:
        """
        Process multiple queries in batch.
        
        Args:
            queries: List of user queries
            
        Returns:
            List of processing results
        """
        results = []
        
        for i, query in enumerate(queries):
            try:
                self.logger.info(f"Processing batch query {i+1}/{len(queries)}")
                result = self.process_query(query)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error processing batch query {i+1}: {e}")
                results.append({
                    "original_input": query,
                    "error": str(e),
                    "session_id": self.session_id,
                    "timestamp": datetime.now().isoformat()
                })
        
        return results
    
    def get_privacy_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data."""
        vault_summary = self.vault.get_vault_summary()
        
        return {
            "vault_summary": vault_summary,
            "session_info": {
                "session_id": self.session_id,
                "model_name": self.model_name,
                "ollama_status": "connected"
            },
            "privacy_stats": vault_summary["today_stats"]
        }
    
    def export_audit_log(self, limit: int = 1000) -> List[Dict]:
        """Export audit log for compliance reporting."""
        cursor = self.vault.conn.cursor()
        cursor.execute(
            "SELECT operation, pii_type, placeholder, timestamp, session_id FROM audit_log ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        
        columns = [description[0] for description in cursor.description]
        audit_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return audit_data
    
    def clear_session_data(self):
        """Clear current session data and start new session."""
        self.session_id = str(uuid.uuid4())
        self.logger.info(f"Started new session: {self.session_id}")
    
    def health_check(self) -> Dict:
        """Perform health check of the privacy engine."""
        health_status = {
            "vault_connection": "healthy",
            "ollama_connection": "healthy",
            "model_available": True,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test vault
            test_text = "Test email: test@example.com"
            redacted, mapping = self.vault.redact_with_mapping(test_text, "health_check")
            health_status["vault_functionality"] = "healthy"
            
        except Exception as e:
            health_status["vault_connection"] = f"unhealthy: {e}"
        
        try:
            # Test Ollama
            models = ollama.list()
            health_status["model_available"] = self.model_name in [m['name'] for m in models['models']]
            
        except Exception as e:
            health_status["ollama_connection"] = f"unhealthy: {e}"
            health_status["model_available"] = False
        
        return health_status
    
    def close(self):
        """Close the privacy engine and cleanup resources."""
        self.logger.info("Shutting down Privacy Engine")
        if self.vault:
            self.vault.close()

# --- TEST ---
if __name__ == "__main__":
    # Initialize the engine
    engine = PrivacyEngine()
    
    # Test queries with PII and Indian IDs
    test_queries = [
        "My name is Rahul Sharma and my email is rahul.sharma@gmail.com. Can you help me?",
        "I need to update my PAN number ABCDE1234F and phone +91-9876543210.",
        "My Aadhaar is 2345 6789 0123. What documents do I need for verification?",
        "Contact me at priya.patel@company.com or call 9876543210 for business inquiry."
    ]
    
    print("=== PRIVACY ENGINE TEST ===")
    
    # Process single query
    print("\n--- Single Query Test ---")
    result = engine.process_query(test_queries[0])
    
    print(f"Original: {result['original_input']}")
    print(f"Redacted: {result['redacted_input']}")
    print(f"AI Response: {result['ai_response']}")
    print(f"Final: {result['final_response']}")
    print(f"PII Detected: {result['pii_detected']}")
    print(f"Processing Time: {result['processing_time']:.2f}s")
    
    # Health check
    print("\n--- Health Check ---")
    health = engine.health_check()
    for key, value in health.items():
        print(f"{key}: {value}")
    
    # Dashboard data
    print("\n--- Dashboard Data ---")
    dashboard = engine.get_privacy_dashboard_data()
    print(f"Total Mappings: {dashboard['vault_summary']['total_mappings']}")
    print(f"Today's Stats: {dashboard['privacy_stats']}")
    
    engine.close()
