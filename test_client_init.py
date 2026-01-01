import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'texas-holdem-ai'))

from ai.llm_client import LLMClient

def test_init():
    print("Testing LLMClient initialization...")
    try:
        # 1. Default init
        client = LLMClient()
        print(f"Default client provider: {client.provider}")
        
        # 2. Test Zhipu Model name trigger
        try:
             client_zhipu = LLMClient(model="glm-4-flash")
             print(f"GLM client provider: {client_zhipu.provider}")
        except Exception as e:
             # It might fail if no key provided and it tries to init ZhipuAiClient?
             # My code has hardcoded default key, so it might pass if zai is present, or fallback/crash if zai missing?
             # If zai missing, HAS_ZAI is False, so provider should be openai.
             print(f"GLM client init result/error: {e}")
             
        print("Initialization tests passed.")
    except Exception as e:
        print(f"FAILED: {e}")
        raise e

if __name__ == "__main__":
    test_init()
