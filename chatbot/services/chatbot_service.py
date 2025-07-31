from django.conf import settings
from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph

from chatbot.models import Conversation, Message
from chatbot.services.agents.domain_agent import domain_agent
from chatbot.services.state import State


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
        self.graph_builder.add_node("chatbot", lambda state: domain_agent(state, self.llm))
        self.graph_builder.add_edge(START, "chatbot")
        self.graph_builder.add_edge("chatbot", END)
        self.graph = self.graph_builder.compile()
    
    def get_response(self, user_message: str, user) -> str:
        """Get a response from the chatbot for a user message."""
        try:
            # Get or create conversation for this user
            conversation, created = Conversation.objects.get_or_create(user=user)
            
            # Save user message
            Message.objects.create(
                conversation=conversation,
                role=Message.RoleChoices.USER,
                content=user_message
            )
            
            # Get conversation history
            messages = []
            for msg in conversation.messages.all():
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Get response from LLM
            result = self.graph.invoke({"messages": messages})
            assistant_response = result["messages"][-1].content
            
            # Save assistant response
            Message.objects.create(
                conversation=conversation,
                role=Message.RoleChoices.ASSISTANT,
                content=assistant_response
            )
            
            return assistant_response
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