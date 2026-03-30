import ollama
from redactor import PrivacySentry # Import the class we made yesterday

class PrivateBrain:
    def __init__(self):
        self.sentry = PrivacySentry()
        self.model = "llama3.2:1b"

    def talk_privately(self, user_input):
        # 1. Redact the user input
        # Note: We'll update your redactor.py to return the mapping next!
        redacted_text, redaction_map = self.sentry.redact_with_mapping(user_input)
        
        print(f"\n[DEBUG] Sent to Cloud: {redacted_text}")

        # 2. Get response from Local Ollama
        response = ollama.chat(model=self.model, messages=[
            {'role': 'user', 'content': redacted_text},
        ])
        
        ai_response = response['message']['content']
        print(f"[DEBUG] Raw AI Response: {ai_response}")

        # 3. Re-hydrate (Put the names back in)
        final_output = ai_response
        for placeholder, real_value in redaction_map.items():
            final_output = final_output.replace(placeholder, real_value)
            
        return final_output

# --- TEST ---
if __name__ == "__main__":
    brain = PrivateBrain()
    user_msg = "My name is Honey Khandelwal. Tell me a 1-sentence greeting."
    print(f"User: {user_msg}")
    
    result = brain.talk_privately(user_msg)
    print(f"AI: {result}")