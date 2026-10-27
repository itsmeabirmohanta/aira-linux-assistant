"""
Google Gemini AI provider implementation for ARIA.
Supports Gemini 2.0 Flash / 1.5 Pro with multimodal image inputs and native function calling.
"""

from __future__ import annotations
import io
from typing import List, Dict, Any, Optional
from aria.utils.logger import logger
from aria.config import config
from aria.providers.base import BaseProvider, AgentMessage, ProviderResponse, ToolCall


class GeminiProvider(BaseProvider):
    def __init__(self):
        self.api_key = config.gemini_api_key
        self.model_name = "gemini-2.0-flash"
        self._client = None
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai = genai
            self._client = genai.GenerativeModel(
                model_name=self.model_name,
            )
            logger.info(f"Gemini provider initialized with model {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize google.generativeai: {e}")

    async def generate_response(
        self,
        messages: List[AgentMessage],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        if not self.api_key:
            return ProviderResponse(
                text="Error: GEMINI_API_KEY is not configured in .env file.",
                tool_calls=[],
            )

        try:
            import google.generativeai as genai

            # Convert tools to Gemini format
            gemini_tools = []
            for t in tools:
                # Wrap as declarations
                gemini_tools.append({
                    "function_declarations": [{
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"],
                    }]
                })

            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt,
                tools=gemini_tools if gemini_tools else None,
            )

            # Build Gemini history
            contents = []
            for msg in messages:
                parts = []
                if msg.image is not None:
                    # Multimodal screenshot
                    parts.append(msg.image)

                if msg.content:
                    parts.append(msg.content)

                if msg.role == "user":
                    contents.append({"role": "user", "parts": parts})
                elif msg.role == "assistant":
                    if msg.tool_calls:
                        # Represent tool call
                        for tc in msg.tool_calls:
                            parts.append({
                                "function_call": {
                                    "name": tc.name,
                                    "args": tc.arguments,
                                }
                            })
                    contents.append({"role": "model", "parts": parts})
                elif msg.role == "tool":
                    contents.append({
                        "role": "function",
                        "parts": [{
                            "function_response": {
                                "name": msg.name or "tool",
                                "response": {"result": msg.content},
                            }
                        }],
                    })

            response = await model.generate_content_async(contents)

            extracted_text = ""
            extracted_tool_calls: List[ToolCall] = []

            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        extracted_text += part.text
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        args = dict(fc.args) if hasattr(fc, "args") else {}
                        extracted_tool_calls.append(ToolCall(name=fc.name, arguments=args))

            return ProviderResponse(
                text=extracted_text,
                tool_calls=extracted_tool_calls,
            )

        except Exception as e:
            logger.error(f"Gemini API request error: {e}")
            return ProviderResponse(
                text=f"Gemini API Error: {str(e)}",
                tool_calls=[],
            )
