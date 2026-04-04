import logging
import requests
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
from huggingface_hub import InferenceClient
from vault import IdentityVault

class PrivacyEngine:
    def __init__(self, inference_mode="huggingface", model_name=None):
        """Initialize the privacy engine with modern HuggingFace InferenceClient."""
        self.inference_mode = "huggingface"
        self.model_name = model_name or "meta-llama/Llama-3.2-1B-Instruct"
        self.vault = IdentityVault()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # Initialize InferenceClient
        self.client = None
        self._initialize_client()
        
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _initialize_client(self):
        """Initialize the HuggingFace InferenceClient."""
        try:
            token = st.secrets.get('HUGGINGFACE_API_TOKEN', '')
            if token:
                # Check if it's a valid HuggingFace token (starts with hf_)
                if token.startswith('hf_'):
                    self.client = InferenceClient(
                        model=self.model_name,
                        token=token,
                        timeout=60
                    )
                    self.logger.info(f"InferenceClient initialized with model: {self.model_name}")
                else:
                    # Non-HuggingFace token - don't initialize client
                    self.logger.warning("Non-HuggingFace API key detected, running in local mode")
                    self.client = None
                    self.connection_message = "⚠️ Invalid API Key: Please use HuggingFace token (starts with hf_)"
            else:
                self.logger.warning("No API token found, running in local mode")
                self.client = None
                self.connection_message = "⚠️ Connection Pending: Please add HuggingFace API Key to Secrets"
        except Exception as e:
            self.logger.error(f"Failed to initialize InferenceClient: {e}")
            self.client = None
            self.connection_message = f"⚠️ Connection Error: {str(e)}"
    
    def process_query(self, query: str) -> str:
        """Process user query through HuggingFace InferenceClient."""
        try:
            if not self.client:
                return self._get_local_response(query)
            
            # Use chat_completion instead of text_generation
            messages = [
                {"role": "system", "content": "You are a Privacy-First Assistant. You will receive text containing placeholders like [PERSON_1] or [AADHAAR_1]. These are safe tokens. Do not refuse to process them. Use these tokens in your response exactly as they are. You do not have access to real data, and that is intentional for security."},
                {"role": "user", "content": query}
            ]
            
            # Use chat_completion for conversational models
            response = self.client.chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            # Extract the assistant's response
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                return "I understand your privacy-related question. Let me help you with that."
                
        except Exception as e:
            error_msg = f"AI Error: {str(e)}"
            self.logger.error(error_msg)
            
            # Show error in sidebar if possible
            try:
                st.sidebar.error(error_msg)
            except:
                pass
            
            return self._get_local_response(query)
    
    def _get_local_response(self, query: str) -> str:
        """Get contextual response when API is not available."""
        user_query = query.lower()
        
        if "aadhaar" in user_query:
            return "I understand you're asking about Aadhaar details. For official Aadhaar updates, please visit the UIDAI website at uidai.gov.in or your nearest Aadhaar center. I can help you understand PII protection while you handle your Aadhaar matters."
        elif "phone" in user_query or "call" in user_query:
            return "I understand you want to share contact information. Your phone number has been protected for privacy. I can help you with questions about secure communication and data protection."
        elif "email" in user_query:
            return "I see you're asking about email communication. Your email has been protected for privacy. I can assist with questions about secure email practices and data protection."
        elif "pan" in user_query:
            return "I understand you're asking about PAN card details. For official PAN services, please visit the Income Tax Department website at incometaxindia.gov.in. I can help you understand PII protection while you handle your PAN matters."
        else:
            return "I'm your privacy assistant! I can help you with questions about data protection, PII detection, secure communication, and privacy best practices. Since we're running in local mode without an API token, I'm providing contextual assistance based on your query."
    
    def health_check(self) -> Dict:
        """Perform health check of the privacy engine."""
        health_status = {
            "vault_connection": "healthy",
            "inference_connection": "local_mode",
            "model_available": False,
            "inference_mode": self.inference_mode,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add connection message if available
        if hasattr(self, 'connection_message'):
            health_status["connection_message"] = self.connection_message
        
        try:
            test_text = "Test email: test@example.com"
            redacted, mapping = self.vault.redact_with_mapping(test_text, 1, "health_check")
            health_status["vault_functionality"] = "healthy"
            
        except Exception as e:
            health_status["vault_connection"] = f"unhealthy: {e}"
        
        # Test AI connection only if we have a valid client
        if self.client:
            try:
                # Simple test query
                test_response = self.client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10,
                    temperature=0.1
                )
                health_status["inference_connection"] = "healthy"
                health_status["model_available"] = True
            except Exception as e:
                health_status["inference_connection"] = f"unhealthy: {e}"
                health_status["model_available"] = False
        else:
            # No client - check if we have a valid reason
            if hasattr(self, 'connection_message'):
                if "Invalid API Key" in self.connection_message:
                    health_status["inference_connection"] = "invalid_key"
                elif "Connection Pending" in self.connection_message:
                    health_status["inference_connection"] = "no_key"
                else:
                    health_status["inference_connection"] = "local_mode"
            else:
                health_status["inference_connection"] = "local_mode"
            health_status["model_available"] = False
        
        return health_status
