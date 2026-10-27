"""
OpenAI AI provider implementation for ARIA.
Supports GPT-4o with vision and function/tool calling.
"""

import json
from aria.utils.logger import logger
from aria.config import config
from aria.providers.base import BaseProvider, AgentMessage, ProviderResponse, ToolCall
from aria.tools.screen import encode_image_base64


class OpenAIProvider(BaseProvider):
    def __init__(self):
        self.api_key = config.openai_api_key
        self.model_name = "gpt-4o"
        self._client = None
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    async def generate_response(
        self,
        messages: List[AgentMessage],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        if not self._client:
            return ProviderResponse(text="Error: OPENAI_API_KEY is not configured.", tool_calls=[])

        try:
            formatted_messages = [{"role": "system", "content": system_prompt}]

            for msg in messages:
                if msg.role == "user":
                    content_parts = []
                    if msg.content:
                        content_parts.append({"type": "text", "text": msg.content})
                    if msg.image:
                        b64_img = encode_image_base64(msg.image)
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                        })
                    formatted_messages.append({"role": "user", "content": content_parts})
                elif msg.role == "assistant":
                    m = {"role": "assistant", "content": msg.content or ""}
                    if msg.tool_calls:
                        m["tool_calls"] = [
                            {
                                "id": tc.id or f"call_{i}",
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": json.dumps(tc.arguments),
                                },
                            }
                            for i, tc in enumerate(msg.tool_calls)
                        ]
                    formatted_messages.append(m)
                elif msg.role == "tool":
                    formatted_messages.append({
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id or "call_0",
                        "content": str(msg.content),
                    })

            openai_tools = [
                {"type": "function", "function": t}
                for t in tools
            ] if tools else None

            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                tools=openai_tools,
                temperature=0.2,
            )

            choice = response.choices[0]
            text = choice.message.content or ""
            extracted_tools = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}
                    extracted_tools.append(ToolCall(name=tc.function.name, arguments=args, id=tc.id))

            return ProviderResponse(text=text, tool_calls=extracted_tools)

        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            return ProviderResponse(text=f"OpenAI Error: {e}", tool_calls=[])
