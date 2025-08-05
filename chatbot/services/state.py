from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from chatbot.models import Message


class State(TypedDict):
    messages: Annotated[list, add_messages]
    current_message: Message
