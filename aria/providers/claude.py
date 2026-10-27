"""
Anthropic Claude provider implementation for ARIA.
Supports Claude 3.5 Sonnet with vision and tools.
"""

from aria.utils.logger import logger
from aria.config import config
from aria.providers.base import BaseProvider, AgentMessage, ProviderResponse, ToolCall
from aria.tools.screen import encode_image_base64


class ClaudeProvider(BaseProvider):
    def __init__(self):
        self.api_key = config.anthropic_api_key
        self.model_name = "claude-3-5-sonnet-20241022"
        self._client = None
        if self.api_key:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

    async def generate_response(
        self,
        messages: List[AgentMessage],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        if not self._client:
            return ProviderResponse(text="Error: ANTHROPIC_API_KEY is not configured.", tool_calls=[])

        try:
            # Map tools to Anthropic format
            claude_tools = []
            for t in tools:
                claude_tools.append({
                    "name": t["name"],
                    "description": t["description"],
                    "input_schema": t["parameters"],
                })

            formatted_messages = []
            for msg in messages:
                if msg.role == "user":
                    content = []
                    if msg.image:
                        b64 = encode_image_base64(msg.image)
                        content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64,
                            },
                        })
                    if msg.content:
                        content.append({"type": "text", "text": msg.content})
                    formatted_messages.append({"role": "user", "content": content})
                elif msg.role == "assistant":
                    content = []
                    if msg.content:
                        content.append({"type": "text", "text": msg.content})
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            content.append({
                                "type": "tool_use",
                                "id": tc.id or "tool_1",
                                "name": tc.name,
                                "input": tc.arguments,
                            })
                    formatted_messages.append({"role": "assistant", "content": content})
                elif msg.role == "tool":
                    formatted_messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id or "tool_1",
                            "content": str(msg.content),
                        }],
                    })

            response = await self._client.messages.create(
                model=self.model_name,
                system=system_prompt,
                messages=formatted_messages,
                tools=claude_tools if claude_tools else None,
                max_tokens=2048,
            )

            text_parts = []
            extracted_tools = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    extracted_tools.append(ToolCall(name=block.name, arguments=block.input, id=block.id))

            return ProviderResponse(text="".join(text_parts), tool_calls=extracted_tools)

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return ProviderResponse(text=f"Claude Error: {e}", tool_calls=[])
