"""
Core ReAct Agent loop for ARIA.
Coordinates reasoning, vision, tool execution, memory, and user updates.
"""

import json
from typing import AsyncGenerator, Dict, Any, Optional
from PIL import Image
from aria.utils.logger import logger
from aria.config import config
from aria.agent.memory import Memory
from aria.agent.planner import build_system_prompt
from aria.agent.executor import tool_executor
from aria.providers import get_provider
from aria.providers.base import AgentMessage, ToolCall
from aria.tools import TOOL_SCHEMAS
from aria.tools.screen import capture_screen


class AgentCore:
    def __init__(self, memory: Memory, provider: Optional[BaseProvider] = None):
        self.memory = memory
        self.provider = provider
        self.current_session_id: Optional[int] = None
        self.conversation_history: list[AgentMessage] = []

    async def run(
        self,
        user_input: str,
        include_screen: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run agent cycle for a user input.
        Yields status dicts, e.g.:
        {"type": "status", "message": "Analyzing screen..."}
        {"type": "text", "content": "I'm going to open the file..."}
        {"type": "tool_start", "tool": "run_shell", "args": {...}}
        {"type": "tool_end", "tool": "run_shell", "result": {...}}
        {"type": "done", "content": "Task finished"}
        """
        # Session setup
        if self.current_session_id is None:
            self.current_session_id = self.memory.create_session(task=user_input)

        self.memory.add_message(self.current_session_id, "user", user_input)

        # Context search from memory
        past_memories = self.memory.search_past_context(user_input, limit=2)
        system_prompt = build_system_prompt(past_memories)

        # Optional initial screen capture
        current_image: Optional[Image.Image] = None
        if include_screen:
            yield {"type": "status", "message": "Capturing screen context..."}
            try:
                current_image = capture_screen()
            except Exception as e:
                logger.debug(f"Screen capture note: {e}")

        # Append user message
        user_msg = AgentMessage(role="user", content=user_input, image=current_image)
        self.conversation_history.append(user_msg)

        provider = self.provider or get_provider()
        steps = 0
        final_answer = ""

        while steps < config.max_steps:
            steps += 1
            yield {"type": "status", "message": f"Thinking (step {steps})..."}

            # Call AI provider with tool schemas
            response = await provider.generate_response(
                messages=self.conversation_history[-config.context_window:],
                system_prompt=system_prompt,
                tools=TOOL_SCHEMAS,
            )

            # If there's textual output, stream it
            if response.text:
                final_answer += response.text
                yield {"type": "text", "content": response.text}

            # If no tool calls, task is complete
            if not response.tool_calls:
                break

            # Add assistant message with tool calls to history
            assistant_msg = AgentMessage(
                role="assistant",
                content=response.text,
                tool_calls=response.tool_calls,
            )
            self.conversation_history.append(assistant_msg)

            # Execute tool calls
            for tc in response.tool_calls:
                yield {"type": "tool_start", "tool": tc.name, "args": tc.arguments}

                result = await tool_executor.execute(tc)

                # Check if tool produced a new screenshot image
                tool_image = result.pop("_image", None)

                # Format tool output as string
                result_str = json.dumps(result, ensure_ascii=False)
                yield {"type": "tool_end", "tool": tc.name, "result": result}

                # Add tool result to history
                tool_msg = AgentMessage(
                    role="tool",
                    name=tc.name,
                    content=result_str,
                    tool_call_id=tc.id or f"call_{tc.name}",
                    image=tool_image,
                )
                self.conversation_history.append(tool_msg)

        # Final record in database
        self.memory.add_message(self.current_session_id, "assistant", final_answer)
        self.memory.update_summary(self.current_session_id, summary=final_answer[:200])

        yield {"type": "done", "content": final_answer}
