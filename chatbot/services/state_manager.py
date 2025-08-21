from langchain_core.messages import HumanMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES, RemoveMessage


class StateManager:
    """Manages LangGraph conversation state operations."""

    def __init__(self, graph):
        self.graph = graph

    def get_thread_config(self, user):
        """Get LangGraph configuration for a user's thread."""
        return {"configurable": {"thread_id": f"user_{user.id}"}}

    def get_conversation_state(self, user):
        """Get the current LangGraph state for a user's conversation thread."""
        config = self.get_thread_config(user)
        return self.graph.get_state(config)

    def get_conversation_history(self, user, limit=None):
        """Get conversation history from LangGraph state."""
        state = self.get_conversation_state(user)
        messages = state.values.get("messages", [])
        return messages[-limit:] if limit else messages

    def clear_conversation(self, user):
        """Clear all messages from a user's conversation thread."""
        config = self.get_thread_config(user)
        self.graph.update_state(config, {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]})

    def prepare_messages_for_graph(self, user, new_message_content):
        """Prepare message list for graph processing."""
        # Get current messages from state
        state = self.get_conversation_state(user)
        current_messages = state.values.get("messages", [])
        
        # Add new user message
        new_messages = current_messages + [HumanMessage(content=new_message_content)]
        
        return new_messages