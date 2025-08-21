import sqlite3

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from chatbot.services.agents.domain_agent import domain_agent
from chatbot.services.agents.safety_agent import safety_agent
from chatbot.services.state import State


class GraphBuilder:
    """Responsible for building and configuring the LangGraph conversation graph."""

    def __init__(self, llm):
        self.llm = llm

    def build_graph(self):
        """Build the complete conversation graph with safety and domain agents."""
        graph_builder = StateGraph(State)
        
        # Add nodes
        graph_builder.add_node("safety", lambda state: safety_agent(state, self.llm))
        graph_builder.add_node("chatbot", lambda state: domain_agent(state, self.llm))

        # Define conditional flow
        def should_continue(state):
            """Check if safety agent blocked the message."""
            messages = state.get("messages", [])
            if messages and messages[-1].type == "ai":
                return "end"
            return "continue"

        # Define graph flow: START -> safety -> (conditional) -> chatbot/END
        graph_builder.add_edge(START, "safety")
        graph_builder.add_conditional_edges("safety", should_continue, {"continue": "chatbot", "end": END})
        graph_builder.add_edge("chatbot", END)

        # Add checkpointer for state persistence
        conn = sqlite3.connect("chatguard_checkpoints.sqlite", check_same_thread=False)
        checkpointer = SqliteSaver(conn)

        return graph_builder.compile(checkpointer=checkpointer)


class LLMFactory:
    """Factory for creating and configuring language models."""

    @staticmethod
    def create_llm():
        """Create and configure the language model."""
        from django.conf import settings
        
        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in Django settings")
        
        return init_chat_model("anthropic:claude-3-5-sonnet-latest")