import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from chatbot.models import ComplianceCheck, ComplianceStatus, SafetyEvent, ViolationType
from chatbot.services.constants import (
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
        reasoning = extract_xml(response_content, "reasoning") or "No reasoning provided"
        status = (extract_xml(response_content, "status") or SAFETY_STATUS_APPROVE).upper()
        violation_type_str = (extract_xml(response_content, "violation_type") or "NONE").upper()

        message = state["current_message"]

        # Map violation type string to enum
        violation_type_map = {
            "JAILBREAK": ViolationType.JAILBREAK,
            "HARMFUL": ViolationType.HARMFUL,
            "ABUSE": ViolationType.ABUSE,
            "NONE": None,
        }
        violation_type = violation_type_map.get(violation_type_str, None)

        # Create compliance check
        if status == SAFETY_STATUS_APPROVE:
            ComplianceCheck.objects.create(
                message=message, status=ComplianceStatus.APPROVED, violation_type=violation_type, reason=reasoning
            )
            logger.info(f"✅ APPROVED: {last_message.content[:100]}...")

        elif status == SAFETY_STATUS_REJECT:
            compliance_check = ComplianceCheck.objects.create(
                message=message, status=ComplianceStatus.REJECTED, violation_type=violation_type, reason=reasoning
            )

            # Create safety event
            SafetyEvent.objects.create(
                event_type=SafetyEvent.EventType.QUERY_BLOCKED, compliance_check=compliance_check
            )

            logger.warning(f"🚫 REJECTED: {last_message.content[:100]}...")
            return {"messages": [AIMessage(content=SAFETY_REJECTION_MESSAGE)]}

        # Message approved, pass through
        return state

    except Exception as e:
        logger.error(f"Error in safety check: {str(e)}")
        # On error, default to accepting to avoid blocking legitimate requests
        return state
