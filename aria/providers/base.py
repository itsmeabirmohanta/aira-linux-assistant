"""
Base abstract class for all AI providers in ARIA.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from PIL import Image


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class AgentMessage:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # for tool role
    image: Optional[Image.Image] = None  # screenshot attachment if any


@dataclass
class ProviderResponse:
    text: str
    tool_calls: List[ToolCall]
    finish_reason: str = "stop"


class BaseProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[AgentMessage],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> ProviderResponse:
        """
        Generate model response, optionally invoking tool calls.
        """
        pass
