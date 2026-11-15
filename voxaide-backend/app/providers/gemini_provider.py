import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.providers.base import LLMProvider, LLMResponse, ToolCallRequest
from app.core.logging import logger

FALLBACK_MODELS = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-2.5-flash",
]

class GeminiProvider(LLMProvider):
    """
    Google Gemini implementation of LLMProvider with automatic rate-limit cascade.
    Defaults to gemini-1.5-flash for generous Free-Tier quotas (1500 req/day).
    """

    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("GeminiProvider initialized without GEMINI_API_KEY.")

    def _get_candidate_models(self) -> List[str]:
        """Returns prioritized list of models to try, starting with self.model_name."""
        candidates = [self.model_name]
        for m in FALLBACK_MODELS:
            if m not in candidates:
                candidates.append(m)
        return candidates

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3
    ) -> LLMResponse:
        candidate_models = self._get_candidate_models()
        last_error = None

        generation_config = genai.types.GenerationConfig(
            temperature=temperature
        )

        formatted_history = []
        if history:
            for turn in history:
                role = "user" if turn.get("role") == "user" else "model"
                formatted_history.append({
                    "role": role,
                    "parts": [turn.get("content", "")]
                })

        for candidate in candidate_models:
            try:
                model = genai.GenerativeModel(
                    model_name=candidate,
                    system_instruction=system_instruction if system_instruction else None,
                    generation_config=generation_config
                )

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

                # If this model succeeded and was a fallback, remember it
                if candidate != self.model_name:
                    logger.info(f"Gemini model cascade switched active model from {self.model_name} to {candidate}")
                    self.model_name = candidate

                return LLMResponse(
                    content=content.strip(),
                    tool_calls=tool_calls,
                    finish_reason="stop"
                )

            except Exception as e:
                err_str = str(e)
                last_error = e
                # Check if it's a quota/rate-limit or model not found error that we should cascade
                is_quota_or_model_error = any(kw in err_str.lower() for kw in [
                    "quota", "429", "rate limit", "resourceexhausted", "not found", "404", "unavailable"
                ])
                if is_quota_or_model_error:
                    logger.warning(
                        f"Gemini model '{candidate}' encountered quota/model error. Trying next fallback model.",
                        error=err_str[:200]
                    )
                    continue
                else:
                    # Non-quota error (e.g. fatal payload error), log and re-raise
                    logger.error("GeminiProvider generation error", error=err_str, model=candidate)
                    raise e

        logger.error("All Gemini candidate models exhausted or rate-limited", error=str(last_error))
        raise last_error or RuntimeError("All Gemini candidate models failed.")
