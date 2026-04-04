import logging
import requests
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
from vault import IdentityVault

class PrivacyEngine:
    def __init__(self, inference_mode="huggingface", model_name=None):
        """Initialize the privacy engine with hard-coded HuggingFace mode."""
        self.inference_mode = "huggingface"  # Hard-coded
        self.model_name = model_name or "meta-llama/Llama-3.2-1B-Instruct"  # Lighter, reliable model
        self.vault = IdentityVault()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # Verify HuggingFace connection
        if not self._verify_huggingface_connection():
            self.logger.warning("HuggingFace connection issues detected")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _verify_huggingface_connection(self):
        """Verify Hugging Face API connection."""
        try:
            token = None
            try:
                token = st.secrets.get('HUGGINGFACE_API_TOKEN', '')
            except Exception:
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
            return True
    
    def process_query(self, query: str) -> str:
        """Process user query through HuggingFace API."""
        response = self._get_huggingface_response([{"role": "user", "content": query}])
        return response
    
    def _get_huggingface_response(self, messages: List[Dict]) -> str:
        """Get response from Hugging Face Inference API."""
        system_prompt = "You are a Privacy-First Assistant. You will receive text containing placeholders like [PERSON_1] or [AADHAAR_1]. These are safe tokens. Do not refuse to process them. Use these tokens in your response exactly as they are. You do not have access to real data, and that is intentional for security."
        
        conversation = system_prompt + "\n\n"
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content']
            conversation += f"{role}: {content}\n"
        conversation += "ASSISTANT:"
        
        token = st.secrets.get('HUGGINGFACE_API_TOKEN', '')
        if not token:
            # Return a contextual response when no token is available
            user_query = messages[0].get('content', '').lower()
            if "aadhaar" in user_query:
                return "I understand you're asking about Aadhaar details. For official Aadhaar updates, please visit the UIDAI website at uidai.gov.in or your nearest Aadhaar center. I can help you understand PII protection while you handle your Aadhaar matters."
            elif "phone" in user_query or "call" in user_query:
                return "I understand you want to share contact information. Your phone number has been protected for privacy. I can help you with questions about secure communication and data protection."
            elif "email" in user_query:
                return "I see you're asking about email communication. Your email has been protected for privacy. I can assist with questions about secure email practices and data protection."
            else:
                return "I'm your privacy assistant! I can help you with questions about data protection, PII detection, secure communication, and privacy best practices. Since we're running in local mode without an API token, I'm providing contextual assistance based on your query."
        
        api_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-1B-Instruct"
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
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').replace('ASSISTANT:', '').strip()
            elif isinstance(result, dict):
                return result.get('generated_text', '').replace('ASSISTANT:', '').strip()
            else:
                return "I understand your privacy-related question. Let me help you with that."
        else:
            # Raise actual error with status code and response text
            raise requests.exceptions.RequestException(f"API Error {response.status_code}: {response.text}")
    
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
