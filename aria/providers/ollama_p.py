"""
Ollama local model provider implementation for ARIA.
Supports local models (e.g. llava, llama3.2-vision, mistral, qwen2.5) with zero cloud dependency.
"""

from aria.utils.logger import logger
from aria.config import config
from aria.providers.base import BaseProvider, AgentMessage, ProviderResponse, ToolCall
from aria.tools.screen import encode_image_base64


class OllamaProvider(BaseProvider):
    def __init__(self):
        self.base_url = config.ollama_base_url
        self.model_name = config.ollama_model
        self._client = None
        try:
            import ollama
            self._client = ollama.AsyncClient(host=self.base_url)
        except Exception as e:
            logger.debug(f"Ollama async client init note: {e}")

    async def generate_response(
        self,
        messages: List[AgentMessage],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        try:
            import ollama
            client = self._client or ollama.AsyncClient(host=self.base_url)

            formatted_messages = [{"role": "system", "content": system_prompt}]

            for msg in messages:
                m = {"role": msg.role if msg.role != "tool" else "user", "content": msg.content or ""}
                if msg.image:
                    b64 = encode_image_base64(msg.image)
                    m["images"] = [b64]
                formatted_messages.append(m)

            response = await client.chat(
                model=self.model_name,
                messages=formatted_messages,
                tools=tools if tools else None,
            )

            text = response.get("message", {}).get("content", "")
            raw_tools = response.get("message", {}).get("tool_calls", [])

            extracted_tools = []
            for t in raw_tools:
                fn = t.get("function", {})
                extracted_tools.append(ToolCall(name=fn.get("name"), arguments=fn.get("arguments", {})))

            return ProviderResponse(text=text, tool_calls=extracted_tools)

        except Exception as e:
            logger.error(f"Ollama request error: {e}")
            return ProviderResponse(text=f"Ollama Local Error: {e}", tool_calls=[])
