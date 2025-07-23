from typing import Annotated
from django.conf import settings
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]


class ChatbotService:
    def __init__(self):
        # Load API key from Django settings
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in Django settings")
        
        # Initialize the language model
        self.llm = init_chat_model("anthropic:claude-3-5-sonnet-latest")
        
        # Build the graph
        self.graph_builder = StateGraph(State)
        self.graph_builder.add_node("chatbot", self._chatbot_node)
        self.graph_builder.add_edge(START, "chatbot")
        self.graph_builder.add_edge("chatbot", END)
        self.graph = self.graph_builder.compile()
    
    def _chatbot_node(self, state: State):
        return {"messages": [self.llm.invoke(state["messages"])]}
    
    def get_response(self, user_message: str) -> str:
        """Get a response from the chatbot for a user message."""
        try:
            result = self.graph.invoke({"messages": [{"role": "user", "content": user_message}]})
            return result["messages"][-1].content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def stream_response(self, user_message: str):
        """Stream a response from the chatbot for a user message."""
        try:
            # Stream directly from the LLM instead of through the graph
            messages = [{"role": "user", "content": user_message}]
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
        except Exception as e:
            yield f"Error: {str(e)}"


# Global chatbot instance (initialized once)
_chatbot_instance = None

def get_chatbot():
    """Get or create the global chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = ChatbotService()
    return _chatbot_instance