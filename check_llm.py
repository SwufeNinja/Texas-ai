import sys
import os

# Ensure we can import from the project
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.llm_client import LLMClient

def check_connection():
    print("🚀 Testing LLM Connection...")
    
    # 1. Initialize Client
    try:
        client = LLMClient()
        print(f"✅ Client Initialized. Provider: {client.provider}")
        if client.provider == "openai":
            print(f"   Base URL: {client.client.base_url}")
    except Exception as e:
        print(f"❌ Client Init Failed: {e}")
        return

    # 2. Send Test Message
    print("\n📩 Sending test message: 'Hello, are you ready for Texas Holdem?'...")
    
    messages = [{"role": "user", "content": "Hello, are you ready for Texas Holdem? Reply with JSON: {\"ready\": true}"}]
    
    try:
        # Note: json_mode=True forces JSON object response
        response = client.chat_completion(messages, json_mode=True)
        
        print("\n📥 Response received:")
        print(response)
        
        if "error" in response:
             print(f"\n❌ API returned error: {response['error']}")
        else:
             print(f"\n✅ SUCCESS! LLM is working.")
             
    except Exception as e:
        print(f"\n❌ Request Failed: {e}")

if __name__ == "__main__":
    check_connection()
