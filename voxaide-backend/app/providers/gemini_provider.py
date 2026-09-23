import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.providers.base import LLMProvider, LLMResponse, ToolCallRequest
from app.core.logging import logger

class GeminiProvider(LLMProvider):
    """Google Gemini implementation of LLMProvider using gemini-2.5-flash."""

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("GeminiProvider initialized without GEMINI_API_KEY.")

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3
    ) -> LLMResponse:
        try:
            # Build generative model with system instruction
            generation_config = genai.types.GenerationConfig(
                temperature=temperature
            )
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction if system_instruction else None,
                generation_config=generation_config
            )

            # Convert chat history if present
            formatted_history = []
            if history:
                for turn in history:
                    role = "user" if turn.get("role") == "user" else "model"
                    formatted_history.append({
                        "role": role,
                        "parts": [turn.get("content", "")]
                    })

            chat = model.start_chat(history=formatted_history)
            response = chat.send_message(prompt)

            content = response.text if hasattr(response, "text") and response.text else ""
            
            # Check for function calls / tool requests in candidate parts
            tool_calls = []
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        args = {k: v for k, v in fc.args.items()}
                        tool_calls.append(ToolCallRequest(name=fc.name, arguments=args))

            return LLMResponse(
                content=content.strip(),
                tool_calls=tool_calls,
                finish_reason="stop"
            )

        except Exception as e:
            logger.error("GeminiProvider generation error", error=str(e))
            raise e
