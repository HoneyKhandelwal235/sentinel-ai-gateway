from presidio_analyzer import AnalyzerEngine
import spacy

print("--- Starting Privacy Engine Test ---")

try:
    # 1. Test spaCy loading
    analyzer = AnalyzerEngine(default_score_threshold=0.3)
    print("✅ 1. spaCy Model Loaded Successfully!")
    
    # 2. Test Presidio Detection
    analyzer = AnalyzerEngine()
    test_text = "My name is Honey Khandelwal and my email is honey@example.com"
    results = analyzer.analyze(text=test_text, entities=["PERSON", "EMAIL_ADDRESS"], language='en')
    
    print(f"✅ 2. Privacy Engine analyzed the text.")
    print(f"Found {len(results)} sensitive items:")
    
    for res in results:
        print(f"   - Type: {res.entity_type} (Score: {round(res.score, 2)})")

    print("\n--- TEST COMPLETE ---")

except Exception as e:
    print(f"❌ Error occurred: {e}")

input("\nPress Enter to exit...")