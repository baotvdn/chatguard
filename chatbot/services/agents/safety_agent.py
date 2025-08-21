import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from chatbot.constants import (
    SAFETY_PROMPT,
    SAFETY_REJECTION_MESSAGE,
    SAFETY_STATUS_APPROVE,
    SAFETY_STATUS_REJECT,
)
from chatbot.services.state import State
from chatbot.services.utils import extract_xml

logger = logging.getLogger(__name__)


def safety_agent(state: State, llm) -> State:
    """
    Safety agent node that uses LLM to detect and filter harmful messages.
    """
    # Get the last user message
    messages = state["messages"]
    if not messages:
        return state

    last_message = messages[-1]

    # Only check user messages
    if last_message.type != "human":
        return state

    # Use LLM to assess safety
    safety_check_messages = [
        SystemMessage(content=SAFETY_PROMPT),
        HumanMessage(content=f"User message to analyze: {last_message.content}"),
    ]

    try:
        # Get LLM assessment
        response = llm.invoke(safety_check_messages)
        response_content = response.content

        # Extract XML fields
        status = (extract_xml(response_content, "status") or SAFETY_STATUS_APPROVE).upper()

        # Simple safety check without compliance tracking for now
        if status == SAFETY_STATUS_APPROVE:
            logger.info(f"✅ APPROVED: {last_message.content[:100]}...")

        elif status == SAFETY_STATUS_REJECT:
            logger.warning(f"🚫 REJECTED: {last_message.content[:100]}...")
            return {"messages": [AIMessage(content=SAFETY_REJECTION_MESSAGE)]}

        # Message approved, pass through
        return state

    except Exception as e:
        logger.error(f"Error in safety check: {str(e)}")
        # On error, default to accepting to avoid blocking legitimate requests
        return state
