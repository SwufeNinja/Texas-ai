import os
import json
from typing import List, Dict, Any, Optional
import logging

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Try to import zai, otherwise optional
try:
    from zai import ZhipuAiClient
    HAS_ZAI = True
except ImportError:
    HAS_ZAI = False
    # If not found, we might want to alert or define a dummy
    pass

from openai import OpenAI

class LLMClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "glm-4.5-air"):
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided. Set ZHIPU_API_KEY environment variable or pass api_key parameter.")
        self.base_url = base_url
        self.model = model
        self.provider = "openai"

        # Check if we should use ZhipuAI based on model name or availability
        if "glm" in self.model.lower():
            if HAS_ZAI:
                self.provider = "zhipu"
                self.client = ZhipuAiClient(api_key=self.api_key)
            else:
                # Fallback to OpenAI standard but pointing to Zhipu Endpoint if not provided
                self.provider = "openai"
                zhipu_url = "https://open.bigmodel.cn/api/paas/v4/"
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url or os.getenv("OPENAI_BASE_URL") or zhipu_url
                )
        else:
            # Standard OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url or os.getenv("OPENAI_BASE_URL")
            )

    def chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = True) -> Dict[str, Any]:
        """
        Send messages to LLM and get response.
        If json_mode is True, attempts to parse JSON from response.
        """
        try:
            if self.provider == "zhipu":
                 # ZhipuAI specific call structure (matches OpenAI mostly)
                 response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.5
                    # Zhipu SDK might not support response_format={"type": "json_object"} directly or consistently?
                    # test.py didn't use it. Let's assume we don't use it for zhipu or try it.
                    # Best to clean prompt to ask for JSON.
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages, # type: ignore
                    response_format={"type": "json_object"} if json_mode else None,  # pyright: ignore[reportArgumentType]
                    temperature=0.5
                )
            
            # OpenAI 1.x / ZhipuAI response structure
            if not response.choices:
                return {"error": "No choices in response"}
                
            content = response.choices[0].message.content
            
            if content is None:
                 return {"error": "Empty response content", "raw": response}

            if json_mode:
                try:
                    # Clean content (remove markdown backticks if any)
                    clean_content = content.strip()
                    if clean_content.startswith("```json"):
                        clean_content = clean_content[7:]
                    if clean_content.startswith("```"):
                        clean_content = clean_content[3:]
                    if clean_content.endswith("```"):
                        clean_content = clean_content[:-3]
                    
                    return json.loads(clean_content.strip())
                except json.JSONDecodeError:
                    logging.error(f"Failed to parse JSON: {content}")
                    return {"error": "Invalid JSON response", "raw": content}
            
            return {"content": content}
            
        except Exception as e:
            logging.error(f"LLM API Error: {e}")
            return {"error": str(e)}

    def mock_completion(self, action="call", reason="Random move"):
        return {
            "action": action,
            "amount": 0,
            "reasoning": reason,
            "chat": "I'm just a random bot for now."
        }
