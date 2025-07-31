import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from chatbot.services.constants import SAFETY_PROMPT, SAFETY_REJECTION_MESSAGE
from chatbot.services.state import State

logger = logging.getLogger(__name__)


def safety_agent(state: State, llm) -> dict:
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
        decision = response.content.strip().upper()

        # Log the decision with visual indicators
        if decision == "ACCEPT":
            logger.info(f"✅ ACCEPTED: {last_message.content[:100]}...")
        elif decision == "REJECT":
            logger.warning(f"🚫 REJECTED: {last_message.content[:100]}...")
            return {"messages": [AIMessage(content=SAFETY_REJECTION_MESSAGE)]}

        # Message accepted, pass through
        return state

    except Exception as e:
        logger.error(f"Error in safety check: {str(e)}")
        # On error, default to accepting to avoid blocking legitimate requests
        return state
