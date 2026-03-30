from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

class PrivacySentry:
    def __init__(self):
        # This is the 'brain' that identifies names, emails, and phones
        self.analyzer = AnalyzerEngine()
        # This is the 'mask' that replaces them with [PERSON] or [EMAIL]
        self.anonymizer = AnonymizerEngine()

    def redact_with_mapping(self, text):
        results = self.analyzer.analyze(text=text, entities=["PERSON", "EMAIL_ADDRESS"], language='en')
        
        mapping = {}
        for i, res in enumerate(results):
            placeholder = f"[{res.entity_type}_{i+1}]"
            real_value = text[res.start:res.end]
            mapping[placeholder] = real_value
            
        # Manually replace for the test (Basic logic)
        redacted_text = text
        for placeholder, real_value in mapping.items():
            redacted_text = redacted_text.replace(real_value, placeholder)
            
        return redacted_text, mapping
        
    def redact_my_data(self, user_input):
        # 1. Analyze the text to find sensitive info
        results = self.analyzer.analyze(
            text=user_input, 
            entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"], 
            language='en'
        )
        
        # 2. Redact it
        anonymized_result = self.anonymizer.anonymize(
            text=user_input,
            analyzer_results=results
        )
        return anonymized_result.text

# --- QUICK TEST ---
if __name__ == "__main__":
    sentry = PrivacySentry()
    sample_text = "Hi, my name is Honey Khandelwal. My email is honey@example.com and my number is 9876543210."
    
    print("--- ORIGINAL ---")
    print(sample_text)
    
    print("\n--- REDACTED (What the Cloud sees) ---")
    print(sentry.redact_my_data(sample_text))