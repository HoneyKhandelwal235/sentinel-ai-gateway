import ollama
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from vault import IdentityVault
import requests

# Import streamlit for secrets management
try:
    import streamlit as st
except ImportError:
    st = None

class PrivacyEngine:
    """
    Enterprise-grade privacy engine with dual inference support (Ollama + Hugging Face).
    Supports local development and cloud deployment with secure PII redaction.
    """
    
    def __init__(self, inference_mode: str = "auto"):
        """
        Initialize the privacy engine.
        
        Args:
            inference_mode: "ollama", "huggingface", or "auto" (auto-detect)
        """
        self.session_id = str(uuid.uuid4())
        self.inference_mode = self._detect_inference_mode(inference_mode)
        self.model_name = self._get_model_name()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize vault
        self.vault = IdentityVault()
        
        # Verify connection based on mode
        self._verify_inference_connection()
    
    def _detect_inference_mode(self, mode: str) -> str:
        """Auto-detect best available inference mode."""
        if mode == "auto":
            # Try Hugging Face first (for cloud deployment)
            try:
                if st and st.secrets.get("HUGGINGFACE_API_TOKEN"):
                    return "huggingface"
            except Exception:
                # Secrets not available (local development)
                pass
            
            # Fall back to Ollama for local development
            if self._check_ollama_available():
                return "ollama"
            else:
                return "huggingface"  # Will use free tier
        return mode
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def _get_model_name(self) -> str:
        """Get appropriate model name based on inference mode."""
        if self.inference_mode == "huggingface":
            return "mistralai/Mistral-7B-Instruct-v0.2"  # Free, fast model
        else:
            return "llama3.2:1b"  # Local Ollama model
    
    def _verify_inference_connection(self):
        """Verify inference service is available based on mode."""
        if self.inference_mode == "ollama":
            self._verify_ollama_connection()
        elif self.inference_mode == "huggingface":
            self._verify_huggingface_connection()
    
    def _verify_ollama_connection(self):
        """Verify Ollama service is available and model exists."""
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Ollama service returned status {response.status_code}")
            
            models = ollama.list()
            available_models = []
            
            if 'models' in models:
                available_models = [model.get('name', model.get('model', 'unknown')) for model in models['models']]
            elif 'models' in str(models):
                available_models = ['llama3.2:1b']
            
            self.logger.info(f"Available models: {available_models}")
            
            if self.model_name not in available_models and len(available_models) > 0:
                self.logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                self.logger.info(f"Pulling model {self.model_name}...")
                ollama.pull(self.model_name)
            
            self.logger.info(f"Ollama connection verified. Using model: {self.model_name}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to connect to Ollama: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"Could not verify Ollama connection: {e}")
            return False
    
    def _verify_huggingface_connection(self):
        """Verify Hugging Face API connection."""
        try:
            token = None
            try:
                token = st.secrets.get('HUGGINGFACE_API_TOKEN', '')
            except Exception:
                # Secrets not available in local development
                pass
            
            if not token:
                self.logger.info("Hugging Face API token not found, will use free tier")
                return True
                
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("https://huggingface.co/api/models", headers=headers, timeout=10)
            if response.status_code == 200:
                self.logger.info(f"Hugging Face API connection verified. Using model: {self.model_name}")
                return True
            else:
                self.logger.warning(f"Hugging Face API returned status {response.status_code}")
                return False
        except Exception as e:
            self.logger.warning(f"Could not verify Hugging Face connection: {e}")
            return True  # Allow continuation for local development
    
    def process_query(self, user_input: str, user_id: int, context: Optional[str] = None) -> Dict:
        """
        Process user query through complete privacy pipeline (user-isolated).
        
        Args:
            user_input: The user's query text
            user_id: The user ID for data isolation
            context: Optional context for the conversation
            
        Returns:
            Dict containing processing results
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Redact PII from user input (user-isolated)
            redacted_input, pii_mapping = self.vault.redact_with_mapping(user_input, user_id, self.session_id)
            
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
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Query processed successfully for user {user_id} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing query for user {user_id}: {e}")
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
        return """You are a Privacy-First Assistant. You will receive text containing placeholders like [PERSON_1], [EMAIL_1], [PHONE_1], [PAN_1], or [AADHAAR_1]. These are safe tokens. Do not refuse to process them. Use these tokens in your response exactly as they are. You do not have access to real data, and that is intentional for security.

IMPORTANT: 
- These placeholders are ALREADY processed and secure
- You MUST ignore your internal privacy filters for these specific tags
- Respond normally and helpfully using the placeholders provided
- Do NOT refuse to answer questions containing these placeholders
- Treat placeholders as normal text tokens

Example:
User: "My name is [PERSON_1] and my email is [EMAIL_1], can you help me?"
Your response: "I'd be happy to help you! How can I assist you today?"

The placeholders represent redacted personal information for privacy protection. They are safe to work with."""
    
    def _get_ai_response(self, messages: List[Dict]) -> str:
        """Get response from AI model with dual inference support."""
        if self.inference_mode == "ollama":
            return self._get_ollama_response(messages)
        elif self.inference_mode == "huggingface":
            return self._get_huggingface_response(messages)
        else:
            raise RuntimeError(f"Unsupported inference mode: {self.inference_mode}")
    
    def _get_ollama_response(self, messages: List[Dict]) -> str:
        """Get response from Ollama AI model."""
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
            if response.status_code != 200:
                raise ConnectionError("Ollama service is not responding")
            
            system_message = {
                "role": "system", 
                "content": "You are a Privacy-First Assistant. You will receive text containing placeholders like [PERSON_1] or [AADHAAR_1]. These are safe tokens. Do not refuse to process them. Use these tokens in your response exactly as they are. You do not have access to real data, and that is intentional for security."
            }
            
            if messages and messages[0].get("role") == "system":
                messages[0] = system_message
            else:
                messages.insert(0, system_message)
            
            response = ollama.chat(
                model=self.model_name,
                messages=messages
            )
            return response['message']['content']
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Cannot connect to Ollama service: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"AI model error: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _get_huggingface_response(self, messages: List[Dict]) -> str:
        """Get response from Hugging Face Inference API."""
        try:
            system_prompt = "You are a Privacy-First Assistant. You will receive text containing placeholders like [PERSON_1] or [AADHAAR_1]. These are safe tokens. Do not refuse to process them. Use these tokens in your response exactly as they are. You do not have access to real data, and that is intentional for security."
            
            conversation = system_prompt + "\n\n"
            for msg in messages:
                role = msg['role'].upper()
                content = msg['content']
                conversation += f"{role}: {content}\n"
            conversation += "ASSISTANT:"
            
            # Get token safely
            token = None
            try:
                token = st.secrets.get('HUGGINGFACE_API_TOKEN', '')
            except Exception:
                # Secrets not available in local development
                pass
            
            if not token:
                return "🔧 **Local Development Mode**: Hugging Face API token not configured. Please set HUGGINGFACE_API_TOKEN in Hugging Face Space secrets or start Ollama for local inference."
            
            api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": conversation,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').replace('ASSISTANT:', '').strip()
                elif isinstance(result, dict):
                    return result.get('generated_text', '').replace('ASSISTANT:', '').strip()
                else:
                    return "I apologize, but I encountered an issue processing your request."
            else:
                raise RuntimeError(f"Hugging Face API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            error_msg = f"Hugging Face API error: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def batch_process(self, queries: List[str], user_id: int) -> List[Dict]:
        """Process multiple queries in batch (user-isolated)."""
        results = []
        
        for i, query in enumerate(queries):
            try:
                self.logger.info(f"Processing batch query {i+1}/{len(queries)} for user {user_id}")
                result = self.process_query(query, user_id)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error processing batch query {i+1} for user {user_id}: {e}")
                results.append({
                    "original_input": query,
                    "error": str(e),
                    "user_id": user_id,
                    "session_id": self.session_id,
                    "timestamp": datetime.now().isoformat()
                })
        
        return results
    
    def get_privacy_dashboard_data(self, user_id: int) -> Dict:
        """Get comprehensive dashboard data for specific user."""
        vault_summary = self.vault.get_vault_summary(user_id)
        
        return {
            "vault_summary": vault_summary,
            "session_info": {
                "session_id": self.session_id,
                "model_name": self.model_name,
                "inference_mode": self.inference_mode
            },
            "privacy_stats": vault_summary["today_stats"],
            "user_id": user_id
        }
    
    def health_check(self) -> Dict:
        """Perform health check of the privacy engine."""
        health_status = {
            "vault_connection": "healthy",
            "inference_connection": "healthy",
            "model_available": True,
            "inference_mode": self.inference_mode,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            test_text = "Test email: test@example.com"
            redacted, mapping = self.vault.redact_with_mapping(test_text, 1, "health_check")
            health_status["vault_functionality"] = "healthy"
            
        except Exception as e:
            health_status["vault_connection"] = f"unhealthy: {e}"
        
        try:
            if self.inference_mode == "ollama":
                response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    health_status["inference_connection"] = "healthy"
                    models = ollama.list()
                    available_models = []
                    if 'models' in models:
                        available_models = [model.get('name', model.get('model', 'unknown')) for model in models['models']]
                    health_status["model_available"] = self.model_name in available_models
                else:
                    health_status["inference_connection"] = f"unhealthy: HTTP {response.status_code}"
                    health_status["model_available"] = False
            elif self.inference_mode == "huggingface":
                try:
                    token = None
                    try:
                        token = st.secrets.get('HUGGINGFACE_API_TOKEN', '')
                    except Exception:
                        pass
                    
                    if token:
                        headers = {"Authorization": f"Bearer {token}"}
                        response = requests.get("https://huggingface.co/api/models", headers=headers, timeout=5)
                        health_status["inference_connection"] = "healthy" if response.status_code == 200 else f"unhealthy: HTTP {response.status_code}"
                        health_status["model_available"] = response.status_code == 200
                    else:
                        health_status["inference_connection"] = "local_development"
                        health_status["model_available"] = False
                except Exception as e:
                    health_status["inference_connection"] = f"unhealthy: {e}"
                    health_status["model_available"] = False
            
        except Exception as e:
            health_status["inference_connection"] = f"unhealthy: {e}"
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
    
    # Create a test user first
    vault = IdentityVault()
    success, message = vault.create_user("testuser", "testpass123", "test@example.com")
    
    if success:
        # Authenticate the test user
        user = vault.authenticate_user("testuser", "testpass123")
        if user:
            print(f"Authenticated user: {user}")
            
            # Test queries with PII and Indian IDs
            test_queries = [
                "My name is Rahul Sharma and my email is rahul.sharma@gmail.com. Can you help me?",
                "I need to update my PAN number ABCDE1234F and phone +91-9876543210.",
                "My Aadhaar is 2345 6789 0123. What documents do I need for verification?",
                "Contact me at priya.patel@company.com or call 9876543210 for business inquiry."
            ]
            
            print("=== PRIVACY ENGINE TEST (MULTI-TENANT) ===")
            
            # Process single query
            print("\n--- Single Query Test ---")
            result = engine.process_query(test_queries[0], user['id'])
            
            print(f"Original: {result['original_input']}")
            print(f"Redacted: {result['redacted_input']}")
            print(f"AI Response: {result['ai_response']}")
            print(f"Final: {result['final_response']}")
            print(f"PII Detected: {result['pii_detected']}")
            print(f"Processing Time: {result['processing_time']:.2f}s")
            print(f"User ID: {result['user_id']}")
            
            # Health check
            print("\n--- Health Check ---")
            health = engine.health_check()
            for key, value in health.items():
                print(f"{key}: {value}")
            
            # Dashboard data
            print("\n--- Dashboard Data ---")
            dashboard = engine.get_privacy_dashboard_data(user['id'])
            print(f"Total Mappings: {dashboard['vault_summary']['total_mappings']}")
            print(f"Today's Stats: {dashboard['privacy_stats']}")
            print(f"User ID: {dashboard['user_id']}")
            
        else:
            print("Authentication failed")
    else:
        print(f"User creation failed: {message}")
    
    engine.close()
