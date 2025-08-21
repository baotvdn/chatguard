from chatbot.services.graph_builder import GraphBuilder, LLMFactory
from chatbot.services.response_streamer import ResponseStreamer
from chatbot.services.state_manager import StateManager


class ChatbotService:
    """Main chatbot service orchestrating conversation management."""

    def __init__(self):
        # Initialize components
        self.llm = LLMFactory.create_llm()
        self.graph = GraphBuilder(self.llm).build_graph()
        self.state_manager = StateManager(self.graph)
        self.response_streamer = ResponseStreamer(self.graph, self.state_manager)

    def stream_response(self, user_message: str, user):
        """Stream a response from the chatbot for a user message."""
        return self.response_streamer.stream_response(user_message, user)

    def get_conversation_state(self, user):
        """Get the current LangGraph state for a user's conversation thread."""
        return self.state_manager.get_conversation_state(user)

    def get_conversation_history(self, user, limit=None):
        """Get conversation history from LangGraph state."""
        return self.state_manager.get_conversation_history(user, limit)

    def clear_conversation(self, user):
        """Clear all messages from a user's conversation."""
        return self.state_manager.clear_conversation(user)


# Global chatbot instance (initialized once)
_chatbot_instance = None


def get_chatbot():
    """Get or create the global chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = ChatbotService()
    return _chatbot_instance
